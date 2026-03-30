import re
from typing import Any, Dict
from urllib.parse import urlparse

from langchain_openai import ChatOpenAI

from src.schemas import LLMGrade


REQUIRED_SECTIONS = [
    "Introduction",
    "Key Insights",
    "Detailed Analysis",
    "Limitations / Gaps",
    "Conclusion",
    "References",
]


def _citation_count(report: str) -> int:
    return len(re.findall(r"\[\d+\]", report))


def _section_coverage(report: str) -> float:
    found = 0
    lowered = report.lower()

    for section in REQUIRED_SECTIONS:
        if section.lower() in lowered:
            found += 1

    return found / len(REQUIRED_SECTIONS)


def _source_diversity(sources: list) -> float:
    if not sources:
        return 0.0

    domains = []
    for source in sources:
        try:
            domain = urlparse(source["url"]).netloc.replace("www.", "")
            domains.append(domain)
        except Exception:
            continue

    if not domains:
        return 0.0

    return len(set(domains)) / len(domains)


def _source_count_score(sources: list) -> float:
    return min(len(sources), 8) / 8.0


def llm_grade_report(
    topic: str,
    goal: str,
    report: str,
    model_name: str,
) -> Dict[str, Any]:
    grader = ChatOpenAI(model=model_name, temperature=0).with_structured_output(LLMGrade)

    prompt = f"""
You are grading a research report.

Topic:
{topic}

What a good answer should do:
{goal}

Report:
{report}

Score from 1 to 5:
- completeness
- citation_quality
- clarity
- practical_value

Be strict but fair.
"""
    result = grader.invoke(prompt)
    return result.model_dump()


def grade_run(
    topic: str,
    goal: str,
    result: Dict[str, Any],
    model_name: str,
) -> Dict[str, Any]:
    report = result.get("report", "")
    sources = result.get("sources", [])

    llm_scores = llm_grade_report(
        topic=topic,
        goal=goal,
        report=report,
        model_name=model_name,
    )

    citation_count = _citation_count(report)
    section_coverage = _section_coverage(report)
    source_diversity = _source_diversity(sources)
    source_count_score = _source_count_score(sources)

    llm_quality = (
        llm_scores["completeness"]
        + llm_scores["citation_quality"]
        + llm_scores["clarity"]
        + llm_scores["practical_value"]
    ) / 20.0

    citation_score = min(citation_count, 6) / 6.0

    return {
        "llm_scores": llm_scores,
        "code_scores": {
            "citation_count": citation_count,
            "citation_score": citation_score,
            "section_coverage": section_coverage,
            "source_diversity": source_diversity,
            "source_count_score": source_count_score,
            "source_count": len(sources),
            "llm_quality": llm_quality,
        },
    }