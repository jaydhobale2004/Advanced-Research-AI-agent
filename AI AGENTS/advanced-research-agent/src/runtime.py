from typing import Any, Dict, Optional

from src.config import RuntimeConfig
from src.evolution.registry import load_active_config
from src.graph import build_graph
from src.state import ResearchState


def run_research(
    topic: str,
    runtime_config: RuntimeConfig,
    agent_config: Optional[Dict[str, Any]] = None,
    evaluation_mode: bool = False,
) -> ResearchState:
    active_agent_config = agent_config or load_active_config()

    graph = build_graph(
        config=runtime_config,
        agent_config=active_agent_config,
        evaluation_mode=evaluation_mode,
    )

    initial_state: ResearchState = {
        "topic": topic.strip(),
        "round": 0,
        "max_rounds": active_agent_config.get("max_rounds", runtime_config.max_rounds),
        "sources": [],
        "findings": [],
        "logs": [],
    }

    return graph.invoke(initial_state)