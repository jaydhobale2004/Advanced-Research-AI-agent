from typing import Any, Dict, List


def compute_overall_score(code_scores: Dict[str, Any]) -> float:
    return round(
        (
            0.35 * code_scores["llm_quality"]
            + 0.20 * code_scores["section_coverage"]
            + 0.20 * code_scores["citation_score"]
            + 0.15 * code_scores["source_diversity"]
            + 0.10 * code_scores["source_count_score"]
        ),
        4,
    )


def aggregate_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "overall_score": 0.0,
            "avg_section_coverage": 0.0,
            "avg_citation_score": 0.0,
            "avg_source_diversity": 0.0,
            "avg_llm_quality": 0.0,
        }

    n = len(rows)

    return {
        "overall_score": round(sum(r["overall_score"] for r in rows) / n, 4),
        "avg_section_coverage": round(sum(r["metrics"]["section_coverage"] for r in rows) / n, 4),
        "avg_citation_score": round(sum(r["metrics"]["citation_score"] for r in rows) / n, 4),
        "avg_source_diversity": round(sum(r["metrics"]["source_diversity"] for r in rows) / n, 4),
        "avg_llm_quality": round(sum(r["metrics"]["llm_quality"] for r in rows) / n, 4),
    }