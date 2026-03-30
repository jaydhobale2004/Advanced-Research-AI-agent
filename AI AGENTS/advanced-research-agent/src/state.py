from typing import Any, Dict, List
from typing_extensions import TypedDict


class ResearchState(TypedDict, total=False):
    topic: str
    round: int
    max_rounds: int
    plan: Dict[str, Any]
    sources: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    critique: Dict[str, Any]
    memory_context: str
    report: str
    logs: List[str]


class OptimizerState(TypedDict, total=False):
    base_config: Dict[str, Any]
    baseline_summary: Dict[str, Any]
    failure_report: Dict[str, Any]
    candidate_configs: List[Dict[str, Any]]
    candidate_summaries: List[Dict[str, Any]]
    decision: Dict[str, Any]
    promotion_result: Dict[str, Any]
    logs: List[str]