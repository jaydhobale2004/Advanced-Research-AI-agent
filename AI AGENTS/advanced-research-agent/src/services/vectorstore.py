from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from src.config import DEFAULT_EMBED_MODEL, INDEX_DIR


@lru_cache(maxsize=1)
def get_embeddings() -> NVIDIAEmbeddings:
    return NVIDIAEmbeddings(model=DEFAULT_EMBED_MODEL)


def load_vectorstore() -> Optional[FAISS]:
    index_path = Path(INDEX_DIR)

    if not index_path.exists():
        return None

    try:
        return FAISS.load_local(
            INDEX_DIR,
            get_embeddings(),
            allow_dangerous_deserialization=True,
        )
    except Exception:
        return None


def save_findings_to_memory(topic: str, findings: List[Dict]) -> None:
    if not findings:
        return

    docs: List[Document] = []

    for item in findings:
        source = item["source"]

        text = (
            f"Topic: {topic}\n"
            f"Claim: {item['claim']}\n"
            f"Evidence: {item['evidence']}\n"
            f"Source title: {source['title']}\n"
            f"Source URL: {source['url']}"
        )

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "topic": topic,
                    "title": source["title"],
                    "url": source["url"],
                    "query": source["query"],
                },
            )
        )

    store = load_vectorstore()

    if store is None:
        store = FAISS.from_documents(docs, get_embeddings())
    else:
        store.add_documents(docs)

    Path(INDEX_DIR).mkdir(parents=True, exist_ok=True)
    store.save_local(INDEX_DIR)


def retrieve_memory_context(topic: str, k: int = 4) -> str:
    store = load_vectorstore()
    if store is None:
        return ""

    docs = store.similarity_search(topic, k=k)
    if not docs:
        return ""

    blocks = []
    for i, doc in enumerate(docs, start=1):
        blocks.append(
            f"[Memory {i}] {doc.page_content}\n"
            f"URL: {doc.metadata.get('url', 'n/a')}\n"
        )

    return "\n".join(blocks)