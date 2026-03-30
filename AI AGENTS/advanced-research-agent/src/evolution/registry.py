import json
from copy import deepcopy
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict

REGISTRY_DIR = Path("agent_registry")
ACTIVE_CONFIG_PATH = REGISTRY_DIR / "active_config.json"
LAST_OPTIMIZATION_PATH = REGISTRY_DIR / "last_optimization.json"

DEFAULT_AGENT_CONFIG: Dict[str, Any] = {
    "version": "v1_base",
    "planner_instructions": (
        "Create a sharp research plan. Break the topic into clear subquestions. "
        "Prefer precise search queries and avoid vague phrasing."
    ),
    "research_instructions": (
        "Use only the provided search results. Extract concrete findings grounded in snippets. "
        "Prefer useful, non-duplicate points with clear evidence."
    ),
    "critique_instructions": (
        "Be strict. Mark research insufficient if key tradeoffs, limitations, or decision factors are missing."
    ),
    "writer_instructions": (
        "Write a professional markdown report. Be accurate, practical, and cite claims with numeric references."
    ),
    "search_results_per_query": 5,
    "max_rounds": 2,
    "memory_k": 4
}


def _ensure_registry() -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)


def load_active_config() -> Dict[str, Any]:
    _ensure_registry()

    if not ACTIVE_CONFIG_PATH.exists():
        save_active_config(DEFAULT_AGENT_CONFIG)
        return deepcopy(DEFAULT_AGENT_CONFIG)

    try:
        with ACTIVE_CONFIG_PATH.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except (JSONDecodeError, OSError):
        save_active_config(DEFAULT_AGENT_CONFIG)
        return deepcopy(DEFAULT_AGENT_CONFIG)

    if not isinstance(config, dict):
        save_active_config(DEFAULT_AGENT_CONFIG)
        return deepcopy(DEFAULT_AGENT_CONFIG)

    merged_config = deepcopy(DEFAULT_AGENT_CONFIG)
    merged_config.update(config)
    return merged_config


def save_active_config(config: Dict[str, Any]) -> None:
    _ensure_registry()
    with ACTIVE_CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def save_last_optimization(report: Dict[str, Any]) -> None:
    _ensure_registry()
    with LAST_OPTIMIZATION_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
