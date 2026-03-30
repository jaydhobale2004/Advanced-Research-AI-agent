from typing import Any, Dict, List

from src.config import RuntimeConfig
from src.evals.dataset import load_eval_dataset
from src.evals.graders import grade_run
from src.evals.metrics import aggregate_rows, compute_overall_score
from src.runtime import run_research


def evaluate_agent_config(
    agent_config: Dict[str, Any],
    runtime_config: RuntimeConfig,
) -> Dict[str, Any]:
    dataset = load_eval_dataset()
    rows: List[Dict[str, Any]] = []

    for example in dataset:
        topic = example["topic"]
        goal = example["goal"]

        result = run_research(
            topic=topic,
            runtime_config=runtime_config,
            agent_config=agent_config,
            evaluation_mode=True,
        )

        grading = grade_run(
            topic=topic,
            goal=goal,
            result=result,
            model_name=runtime_config.chat_model,
        )

        code_scores = grading["code_scores"]
        overall_score = compute_overall_score(code_scores)

        rows.append(
            {
                "topic": topic,
                "goal": goal,
                "overall_score": overall_score,
                "metrics": code_scores,
                "llm_scores": grading["llm_scores"],
                "report_preview": result.get("report", "")[:700],
                "source_count": len(result.get("sources", [])),
            }
        )

    return {
        "config_version": agent_config["version"],
        "config": agent_config,
        "rows": rows,
        "aggregate": aggregate_rows(rows),
    }