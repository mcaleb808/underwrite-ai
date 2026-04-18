"""Thin retriever wrapper around the Chroma guidelines collection."""

import chromadb
from chromadb.utils import embedding_functions

from src.config import settings
from src.schemas.decision import GuidelineChunk


def _get_collection(persist_dir: str) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=persist_dir)
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.OPENAI_API_KEY,
        model_name="text-embedding-3-small",
    )
    return client.get_collection("uw_guidelines", embedding_function=ef)


def retrieve(
    query: str,
    persist_dir: str,
    k: int = 5,
) -> list[GuidelineChunk]:
    """Retrieve the top-k guideline chunks matching the query."""
    collection = _get_collection(persist_dir)
    results = collection.query(query_texts=[query], n_results=k)

    chunks = []
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    dists = results["distances"][0] if results["distances"] else []

    for doc, meta, dist in zip(docs, metas, dists, strict=False):
        chunks.append(
            GuidelineChunk(
                rule_id=meta["rule_id"],
                section_title=meta["section"],
                text=doc,
                score=1 - dist,  # convert distance to similarity
            )
        )

    return chunks
