from pprint import pprint

from src.config import DEFAULT_CHAT_MODEL, build_runtime_config, validate_api_keys
from src.evolution.optimizer_graph import build_optimizer_graph


def main():
    runtime_config = build_runtime_config(
        chat_model=DEFAULT_CHAT_MODEL,
        search_results_per_query=5,
        max_rounds=2,
    )

    if not validate_api_keys(runtime_config):
        raise ValueError("Missing NVIDIA_API_KEY or SERPAPI_API_KEY in your .env file.")

    optimizer = build_optimizer_graph(
        runtime_config=runtime_config,
        auto_promote=True,
    )

    result = optimizer.invoke({})

    print("\n=== OPTIMIZER LOGS ===")
    for line in result.get("logs", []):
        print("-", line)

    print("\n=== DECISION ===")
    pprint(result.get("decision", {}))

    print("\n=== PROMOTION RESULT ===")
    pprint(result.get("promotion_result", {}))


if __name__ == "__main__":
    main()
