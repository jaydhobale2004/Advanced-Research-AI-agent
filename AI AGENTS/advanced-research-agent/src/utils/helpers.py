from datetime import datetime
from typing import Any, Dict, List, Tuple

from src.state import ResearchState


def append_log(state: ResearchState, message: str) -> List[str]:
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    return state.get("logs", []) + [f"{timestamp} UTC - {message}"]


def dedupe_sources(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = {item.get("url") for item in existing}
    merged = list(existing)

    for item in incoming:
        url = item.get("url")
        if url and url not in seen:
            merged.append(item)
            seen.add(url)

    return merged


def dedupe_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []

    for item in findings:
        key = (item["claim"].strip().lower(), item["source"]["url"])
        if key not in seen:
            unique.append(item)
            seen.add(key)

    return unique


def format_sources_for_model(sources: List[Dict[str, Any]]) -> str:
    blocks = []

    for idx, source in enumerate(sources):
        blocks.append(
            f"[{idx}]\n"
            f"Title: {source['title']}\n"
            f"URL: {source['url']}\n"
            f"Snippet: {source['snippet']}\n"
            f"Search query: {source['query']}"
        )

    return "\n\n".join(blocks)


def build_reference_registry(findings: List[Dict[str, Any]]) -> Tuple[Dict[str, int], str]:
    url_to_ref: Dict[str, int] = {}
    reference_lines: List[str] = []

    for item in findings:
        source = item["source"]
        url = source["url"]

        if url not in url_to_ref:
            ref_number = len(url_to_ref) + 1
            url_to_ref[url] = ref_number
            reference_lines.append(f"[{ref_number}] {source['title']} — {url}")

    return url_to_ref, "\n".join(reference_lines)


def build_findings_for_writer(findings: List[Dict[str, Any]], url_to_ref: Dict[str, int]) -> str:
    lines = []

    for idx, item in enumerate(findings, start=1):
        source = item["source"]
        ref = url_to_ref[source["url"]]

        lines.append(
            f"{idx}. Claim: {item['claim']}\n"
            f"   Evidence: {item['evidence']}\n"
            f"   Use citation: [{ref}]\n"
            f"   Source: {source['title']}\n"
            f"   URL: {source['url']}"
        )

    return "\n\n".join(lines)