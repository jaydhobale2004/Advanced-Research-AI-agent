from copy import deepcopy
from typing import Any, Dict, List


def build_candidates(base_config: Dict[str, Any], failure_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    problems = set(failure_report.get("problems", []))

    c1 = deepcopy(base_config)
    c1["version"] = f'{base_config["version"]}_cand_citations'
    c1["writer_instructions"] += (
        " Every major factual claim should have an inline numeric citation. "
        "Prefer explicit source-backed statements over broad summaries."
    )
    candidates.append(c1)

    c2 = deepcopy(base_config)
    c2["version"] = f'{base_config["version"]}_cand_critic'
    c2["critique_instructions"] += (
        " Reject shallow coverage. Ask for more research when tradeoffs, limitations, or practical advice are missing."
    )
    c2["max_rounds"] = min(base_config.get("max_rounds", 2) + 1, 3)
    candidates.append(c2)

    c3 = deepcopy(base_config)
    c3["version"] = f'{base_config["version"]}_cand_search'
    c3["search_results_per_query"] = min(base_config.get("search_results_per_query", 5) + 1, 8)
    c3["research_instructions"] += (
        " Prefer covering multiple perspectives and avoid repeatedly using the same kind of source."
    )
    candidates.append(c3)

    c4 = deepcopy(base_config)
    c4["version"] = f'{base_config["version"]}_cand_targeted'

    if "weak_citations" in problems:
        c4["writer_instructions"] += " Be unusually strict about citing factual claims."
    if "missing_sections" in problems:
        c4["writer_instructions"] += " Ensure all required report sections are present and clearly labeled."
    if "low_source_diversity" in problems:
        c4["research_instructions"] += " Seek variety in sources and avoid repeating the same domain."
    if "low_quality_reasoning" in problems:
        c4["planner_instructions"] += " Focus on decision-useful subquestions and tradeoff-oriented search queries."

    candidates.append(c4)

    return candidates