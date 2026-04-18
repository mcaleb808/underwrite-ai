"""Ingest guidelines into Chroma vector store."""

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from src.config import settings
from src.rag.chunks import chunk_markdown


def ingest(md_path: str | Path, persist_dir: str | Path) -> int:
    """Chunk the guidelines markdown and upsert into Chroma.

    Returns the number of chunks ingested.
    """
    client = chromadb.PersistentClient(path=str(persist_dir))
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.OPENAI_API_KEY,
        model_name="text-embedding-3-small",
    )
    collection = client.get_or_create_collection("uw_guidelines", embedding_function=ef)

    text = Path(md_path).read_text()
    chunks = chunk_markdown(text)

    collection.upsert(
        ids=[c["rule_id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"rule_id": c["rule_id"], "section": c["section_title"]} for c in chunks],
    )

    return len(chunks)
