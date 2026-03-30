import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

INDEX_DIR = "faiss_research_memory"
SERPAPI_URL = "https://serpapi.com/search.json"

DEFAULT_CHAT_MODEL = os.getenv("NVIDIA_CHAT_MODEL", "nvidia/nemotron-3-super-120b-a12b")
DEFAULT_EMBED_MODEL = os.getenv("NVIDIA_EMBED_MODEL", "nvidia/nv-embed-v1")


@dataclass
class RuntimeConfig:
    chat_model: str
    embed_model: str
    search_results_per_query: int
    max_rounds: int
    nvidia_api_key: str
    serpapi_api_key: str


def build_runtime_config(
    chat_model: str,
    search_results_per_query: int,
    max_rounds: int,
) -> RuntimeConfig:
    nvidia_api_key = os.getenv("NVIDIA_API_KEY", "")
    serpapi_api_key = os.getenv("SERPAPI_API_KEY", "")

    if nvidia_api_key:
        os.environ["NVIDIA_API_KEY"] = nvidia_api_key

    return RuntimeConfig(
        chat_model=chat_model or DEFAULT_CHAT_MODEL,
        embed_model=DEFAULT_EMBED_MODEL,
        search_results_per_query=search_results_per_query,
        max_rounds=max_rounds,
        nvidia_api_key=nvidia_api_key,
        serpapi_api_key=serpapi_api_key,
    )


def validate_api_keys(config: RuntimeConfig) -> bool:
    return bool(config.nvidia_api_key and config.serpapi_api_key)
