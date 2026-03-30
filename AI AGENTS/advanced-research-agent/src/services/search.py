from typing import Dict, List

import requests

from src.config import SERPAPI_URL


def serpapi_search(query: str, api_key: str, num_results: int = 5) -> List[Dict[str, str]]:
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num_results,
    }

    response = requests.get(SERPAPI_URL, params=params, timeout=45)
    response.raise_for_status()
    payload = response.json()

    sources: List[Dict[str, str]] = []

    for item in payload.get("organic_results", [])[:num_results]:
        url = item.get("link")
        if not url:
            continue

        sources.append(
            {
                "title": item.get("title", "Untitled"),
                "url": url,
                "snippet": item.get("snippet", ""),
                "query": query,
            }
        )

    return sources