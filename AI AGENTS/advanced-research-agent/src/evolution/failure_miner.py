from typing import Any, Dict


def mine_failures(summary: Dict[str, Any]) -> Dict[str, Any]:
    aggregate = summary["aggregate"]

    problems = []

    if aggregate["avg_citation_score"] < 0.5:
        problems.append("weak_citations")

    if aggregate["avg_section_coverage"] < 0.9:
        problems.append("missing_sections")

    if aggregate["avg_source_diversity"] < 0.6:
        problems.append("low_source_diversity")

    if aggregate["avg_llm_quality"] < 0.7:
        problems.append("low_quality_reasoning")

    return {
        "problems": problems,
        "aggregate": aggregate,
    }