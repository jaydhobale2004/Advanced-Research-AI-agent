from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from src.config import RuntimeConfig
from src.evolution.candidate_builder import build_candidates
from src.evolution.eval_runner import evaluate_agent_config
from src.evolution.failure_miner import mine_failures
from src.evolution.promoter import apply_promotion, choose_best_candidate
from src.evolution.registry import load_active_config, save_last_optimization
from src.state import OptimizerState


def build_optimizer_graph(runtime_config: RuntimeConfig, auto_promote: bool = True):
    def log(state: OptimizerState, message: str) -> List[str]:
        return state.get("logs", []) + [message]

    def load_base_config(state: OptimizerState) -> Dict[str, Any]:
        base_config = load_active_config()
        return {
            "base_config": base_config,
            "logs": log(state, f'Loaded active config: {base_config["version"]}'),
        }

    def baseline_eval(state: OptimizerState) -> Dict[str, Any]:
        summary = evaluate_agent_config(state["base_config"], runtime_config)
        return {
            "baseline_summary": summary,
            "logs": log(state, "Finished baseline evaluation."),
        }

    def analyze_failures(state: OptimizerState) -> Dict[str, Any]:
        failure_report = mine_failures(state["baseline_summary"])
        return {
            "failure_report": failure_report,
            "logs": log(state, f"Detected problems: {failure_report['problems']}"),
        }

    def make_candidates(state: OptimizerState) -> Dict[str, Any]:
        candidates = build_candidates(state["base_config"], state["failure_report"])
        return {
            "candidate_configs": candidates,
            "logs": log(state, f"Built {len(candidates)} candidate configs."),
        }

    def evaluate_candidates(state: OptimizerState) -> Dict[str, Any]:
        summaries = []
        for config in state["candidate_configs"]:
            summaries.append(evaluate_agent_config(config, runtime_config))

        return {
            "candidate_summaries": summaries,
            "logs": log(state, "Finished candidate evaluations."),
        }

    def choose_and_promote(state: OptimizerState) -> Dict[str, Any]:
        decision = choose_best_candidate(
            baseline_summary=state["baseline_summary"],
            candidate_summaries=state["candidate_summaries"],
            min_gain=0.05,
        )

        promotion_result = apply_promotion(decision, auto_promote=auto_promote)

        final_report = {
            "base_version": state["base_config"]["version"],
            "baseline_summary": state["baseline_summary"],
            "failure_report": state["failure_report"],
            "candidate_summaries": state["candidate_summaries"],
            "decision": decision,
            "promotion_result": promotion_result,
        }
        save_last_optimization(final_report)

        return {
            "decision": decision,
            "promotion_result": promotion_result,
            "logs": log(state, f"Promotion result: {promotion_result}"),
        }

    graph = StateGraph(OptimizerState)
    graph.add_node("load_base_config", load_base_config)
    graph.add_node("baseline_eval", baseline_eval)
    graph.add_node("analyze_failures", analyze_failures)
    graph.add_node("make_candidates", make_candidates)
    graph.add_node("evaluate_candidates", evaluate_candidates)
    graph.add_node("choose_and_promote", choose_and_promote)

    graph.add_edge(START, "load_base_config")
    graph.add_edge("load_base_config", "baseline_eval")
    graph.add_edge("baseline_eval", "analyze_failures")
    graph.add_edge("analyze_failures", "make_candidates")
    graph.add_edge("make_candidates", "evaluate_candidates")
    graph.add_edge("evaluate_candidates", "choose_and_promote")
    graph.add_edge("choose_and_promote", END)

    return graph.compile()