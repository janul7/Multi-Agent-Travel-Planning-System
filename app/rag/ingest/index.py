from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import chromadb


def upsert_chunks(
    *,
    chroma_path: Path,
    collection_name: str,
    ids: List[str],
    documents: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict],
) -> None:
    chroma_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
