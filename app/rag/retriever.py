from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import chromadb

from app.core.config import settings
from app.rag.ingest.embed import embed_texts


def retrieve(query: str, *, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Returns a list of RAG chunks with citations.
    Distances are cosine distance (0 = most similar).
    """
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    col = client.get_collection(name=settings.chroma_collection)

    q_emb = embed_texts(
        [query],
        model=settings.gemini_embed_model,
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=768,
    )[0]

    res = col.query(
        query_embeddings=[q_emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    out: List[Dict[str, Any]] = []
    for i in range(len(res["ids"][0])):
        md = res["metadatas"][0][i] or {}
        out.append(
            {
                "chunk_id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "score_distance": float(res["distances"][0][i]),
                "source_url": md.get("source_url"),
                "page_title": md.get("page_title"),
                "section_path": md.get("section_path"),
                "attribution": md.get("attribution"),
            }
        )

    return out
