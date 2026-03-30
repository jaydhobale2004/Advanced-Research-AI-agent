import json
from typing import Any, Dict, List, Optional

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ValidationError

from src.config import RuntimeConfig
from src.evolution.registry import load_active_config
from src.schemas import CritiqueResult, FindingBatch, ResearchPlan
from src.services.search import serpapi_search
from src.services.vectorstore import retrieve_memory_context, save_findings_to_memory
from src.state import ResearchState
from src.utils.helpers import (
    append_log,
    build_findings_for_writer,
    build_reference_registry,
    dedupe_findings,
    dedupe_sources,
    format_sources_for_model,
)

def _coerce_structured_output(raw: Any, model_cls: type[BaseModel]) -> BaseModel:
    if isinstance(raw, model_cls):
        return raw

    if isinstance(raw, BaseModel):
        return model_cls.model_validate(raw.model_dump())

    if isinstance(raw, dict):
        return model_cls.model_validate(raw)

    if model_cls is FindingBatch and isinstance(raw, list):
        return model_cls.model_validate({"findings": raw})

    raise TypeError(
        f"Unexpected structured output type for {model_cls.__name__}: {type(raw).__name__}"
    )


def _extract_json_payload(text: str) -> Any:
    candidate = text.strip()

    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()

    start = min([idx for idx in (candidate.find("{"), candidate.find("[")) if idx != -1], default=-1)
    if start > 0:
        candidate = candidate[start:]

    return json.loads(candidate)


def _json_schema_prompt(model_cls: type[BaseModel]) -> str:
    schema = json.dumps(model_cls.model_json_schema(), indent=2)
    return (
        "\nReturn only valid JSON matching this schema. "
        "Do not include markdown fences, commentary, or extra text.\n"
        f"{schema}\n"
    )


def _invoke_structured_with_fallback(
    structured_llm: Any,
    fallback_llm: ChatNVIDIA,
    prompt: str,
    model_cls: type[BaseModel],
) -> BaseModel:
    try:
        raw = structured_llm.invoke(prompt)
        return _coerce_structured_output(raw, model_cls)
    except (TypeError, ValidationError, json.JSONDecodeError, AttributeError):
        fallback_response = fallback_llm.invoke(prompt + _json_schema_prompt(model_cls))
        content = getattr(fallback_response, "content", fallback_response)

        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"{model_cls.__name__} generation returned no usable content.")

        parsed = _extract_json_payload(content)
        return model_cls.model_validate(parsed)


def _default_structured_value(model_cls: type[BaseModel]) -> BaseModel:
    if model_cls is FindingBatch:
        return FindingBatch(findings=[])
    if model_cls is CritiqueResult:
        return CritiqueResult(
            sufficient=False,
            missing_points=["Structured critique generation failed."],
            weak_spots=["Model did not return usable critique content."],
            extra_queries=[],
        )

    raise ValueError(f"No default structured value configured for {model_cls.__name__}.")


def _fallback_findings_from_sources(sources: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    for idx, source in enumerate(sources[:limit]):
        snippet = (source.get("snippet") or "").strip()
        title = (source.get("title") or "Untitled source").strip()
        claim = title.rstrip(" -|:")

        evidence = snippet or f"Relevant source found for query '{source.get('query', 'n/a')}'."
        importance = max(0.3, round(1 - (idx * 0.1), 2))

        findings.append(
            {
                "claim": claim,
                "evidence": evidence,
                "importance": importance,
                "source": source,
            }
        )

    return findings


def build_graph(
    config: RuntimeConfig,
    agent_config: Optional[Dict[str, Any]] = None,
    evaluation_mode: bool = False,
):
    agent_cfg = agent_config or load_active_config()

    planner_base_llm = ChatNVIDIA(model=config.chat_model, temperature=0)
    researcher_base_llm = ChatNVIDIA(model=config.chat_model, temperature=0)
    critic_base_llm = ChatNVIDIA(model=config.chat_model, temperature=0)
    planner_llm = planner_base_llm.with_structured_output(ResearchPlan)
    researcher_llm = researcher_base_llm.with_structured_output(FindingBatch)
    critic_llm = critic_base_llm.with_structured_output(CritiqueResult)
    writer_llm = ChatNVIDIA(model=config.chat_model, temperature=0.2)

    def load_memory(state: ResearchState) -> Dict[str, Any]:
        if evaluation_mode:
            return {
                "memory_context": "",
                "logs": append_log(state, "Skipped FAISS memory in evaluation mode."),
            }

        memory_context = retrieve_memory_context(
            state["topic"],
            k=agent_cfg.get("memory_k", 4),
        )

        return {
            "memory_context": memory_context,
            "logs": append_log(state, "Loaded semantic memory from FAISS."),
        }

    def plan(state: ResearchState) -> Dict[str, Any]:
        prompt = f"""
You are the planning agent in a research workflow.

Planner policy:
{agent_cfg["planner_instructions"]}

Topic:
{state['topic']}

Relevant previous memory (may be empty):
{state.get('memory_context', '')}

Create a focused research plan.

Requirements:
- 3 to 6 subquestions
- 4 to 8 search queries
- success criteria that define what a good answer must cover
- prefer precise, evidence-oriented search queries
"""
        result = _invoke_structured_with_fallback(
            planner_llm,
            planner_base_llm,
            prompt,
            ResearchPlan,
        )

        return {
            "plan": result.model_dump(),
            "logs": append_log(state, "Planner created the research plan."),
        }

    def research(state: ResearchState) -> Dict[str, Any]:
        if state.get("round", 0) == 0:
            active_queries = state["plan"]["search_queries"]
        else:
            active_queries = state["critique"].get("extra_queries", [])

        active_queries = active_queries[:6]
        search_results_per_query = agent_cfg.get(
            "search_results_per_query",
            config.search_results_per_query,
        )

        gathered: List[Dict[str, str]] = []

        for query in active_queries:
            try:
                gathered.extend(
                    serpapi_search(
                        query=query,
                        api_key=config.serpapi_api_key,
                        num_results=search_results_per_query,
                    )
                )
            except Exception as exc:
                gathered.append(
                    {
                        "title": f"Search error for query: {query}",
                        "url": "",
                        "snippet": str(exc),
                        "query": query,
                    }
                )

        valid_gathered = [item for item in gathered if item.get("url")]
        merged_sources = dedupe_sources(state.get("sources", []), valid_gathered)

        if not merged_sources:
            round_number = state.get("round", 0) + 1
            return {
                "round": round_number,
                "sources": [],
                "findings": state.get("findings", []),
                "logs": append_log(
                    state,
                    f"Research round {round_number} found no usable search sources.",
                ),
            }

        source_text = format_sources_for_model(merged_sources)

        extraction_prompt = f"""
You are the research agent.

Research policy:
{agent_cfg["research_instructions"]}

Topic:
{state['topic']}

Plan:
{state['plan']}

Use ONLY the sources below.
Extract up to 8 concrete, non-duplicate findings that directly help answer the topic.
It is better to return fewer findings than to invent or overstate.

Each finding must:
- make one specific claim
- include a short evidence sentence grounded in the source snippet
- point to a source_idx that exists in the source list

Sources:
{source_text}
"""
        try:
            extracted = _invoke_structured_with_fallback(
                researcher_llm,
                researcher_base_llm,
                extraction_prompt,
                FindingBatch,
            )
            extraction_log = None
        except Exception as exc:
            extracted = _default_structured_value(FindingBatch)
            extraction_log = f"Research extraction returned no usable structured findings: {exc}"

        new_findings: List[Dict[str, Any]] = []

        for item in extracted.findings:
            if 0 <= item.source_idx < len(merged_sources):
                source = merged_sources[item.source_idx]
                new_findings.append(
                    {
                        "claim": item.claim,
                        "evidence": item.evidence,
                        "importance": item.importance,
                        "source": source,
                    }
                )

        if not new_findings:
            new_findings = _fallback_findings_from_sources(merged_sources)
            if extraction_log:
                extraction_log = (
                    f"{extraction_log}. Used fallback source-based findings from {len(new_findings)} sources."
                )
            else:
                extraction_log = (
                    f"Research round used fallback source-based findings from {len(new_findings)} sources."
                )

        all_findings = dedupe_findings(state.get("findings", []) + new_findings)

        if not evaluation_mode:
            save_findings_to_memory(state["topic"], new_findings)

        round_number = state.get("round", 0) + 1

        return {
            "round": round_number,
            "sources": merged_sources,
            "findings": all_findings,
            "logs": append_log(
                state,
                extraction_log
                or f"Research round {round_number} completed with {len(new_findings)} new findings.",
            ),
        }

    def critique(state: ResearchState) -> Dict[str, Any]:
        findings = state.get("findings", [])
        url_to_ref, _ = build_reference_registry(findings)
        findings_text = build_findings_for_writer(findings, url_to_ref)

        prompt = f"""
You are the critic agent.

Critique policy:
{agent_cfg["critique_instructions"]}

Topic:
{state['topic']}

Plan:
{state['plan']}

Current findings:
{findings_text}

Decide whether the research is sufficient.

If not sufficient:
- list the missing points
- identify weak spots
- provide 2 to 5 extra search queries to close the gaps
"""
        try:
            result = _invoke_structured_with_fallback(
                critic_llm,
                critic_base_llm,
                prompt,
                CritiqueResult,
            )
            critique_log = "Critic reviewed the current evidence."
        except Exception as exc:
            result = _default_structured_value(CritiqueResult)
            critique_log = f"Critique fallback used because structured output failed: {exc}"

        return {
            "critique": result.model_dump(),
            "logs": append_log(state, critique_log),
        }

    def route_after_critique(state: ResearchState) -> str:
        critique_data = state.get("critique", {})
        enough = critique_data.get("sufficient", False)
        has_more_rounds = state.get("round", 0) < state.get("max_rounds", 2)
        has_extra_queries = bool(critique_data.get("extra_queries"))

        if (not enough) and has_more_rounds and has_extra_queries:
            return "research"

        return "write"

    def write_report(state: ResearchState) -> Dict[str, Any]:
        findings = state.get("findings", [])
        url_to_ref, references_block = build_reference_registry(findings)
        findings_text = build_findings_for_writer(findings, url_to_ref)

        prompt = f"""
You are the final writer agent.

Writer policy:
{agent_cfg["writer_instructions"]}

Write a professional markdown report on:
{state['topic']}

Use only the evidence supplied below.
Use inline numeric citations exactly like [1], [2], [3].
Do not invent sources or citation numbers.

Memory context:
{state.get('memory_context', '')}

Findings:
{findings_text}

Reference registry:
{references_block}

Required sections:
1. Introduction
2. Key Insights
3. Detailed Analysis
4. Limitations / Gaps
5. Conclusion
"""
        report = writer_llm.invoke(prompt).content
        full_report = f"{report}\n\n## References\n{references_block}"

        return {
            "report": full_report,
            "logs": append_log(state, "Writer produced the final report."),
        }

    graph = StateGraph(ResearchState)
    graph.add_node("load_memory", load_memory)
    graph.add_node("plan", plan)
    graph.add_node("research", research)
    graph.add_node("critique", critique)
    graph.add_node("write", write_report)

    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "plan")
    graph.add_edge("plan", "research")
    graph.add_edge("research", "critique")
    graph.add_conditional_edges(
        "critique",
        route_after_critique,
        {
            "research": "research",
            "write": "write",
        },
    )
    graph.add_edge("write", END)

    return graph.compile()
