from typing import Any, Dict, List, Optional

from src.evolution.registry import save_active_config


def choose_best_candidate(
    baseline_summary: Dict[str, Any],
    candidate_summaries: List[Dict[str, Any]],
    min_gain: float = 0.05,
) -> Dict[str, Any]:
    baseline_score = baseline_summary["aggregate"]["overall_score"]

    best: Optional[Dict[str, Any]] = None
    best_score = baseline_score

    for candidate in candidate_summaries:
        score = candidate["aggregate"]["overall_score"]
        if score > best_score:
            best = candidate
            best_score = score

    improvement = round(best_score - baseline_score, 4)

    if best is None or improvement < min_gain:
        return {
            "promote": False,
            "reason": f"No candidate cleared the promotion threshold of {min_gain:.2f}.",
            "baseline_score": baseline_score,
            "winner_score": best_score,
            "improvement": improvement,
            "winner": None,
        }

    return {
        "promote": True,
        "reason": "A better candidate beat the baseline by the required margin.",
        "baseline_score": baseline_score,
        "winner_score": best_score,
        "improvement": improvement,
        "winner": best,
    }


def apply_promotion(decision: Dict[str, Any], auto_promote: bool = True) -> Dict[str, Any]:
    if decision["promote"] and decision["winner"] and auto_promote:
        save_active_config(decision["winner"]["config"])
        return {
            "promoted": True,
            "new_version": decision["winner"]["config"]["version"],
            "reason": decision["reason"],
        }

    return {
        "promoted": False,
        "new_version": None,
        "reason": decision["reason"],
    }