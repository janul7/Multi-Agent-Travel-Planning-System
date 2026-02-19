# app/rag/ingest/run.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.rag.ingest.fetch import fetch_wikivoyage_parse_html, save_raw_page
from app.rag.ingest.clean import clean_raw_file
from app.rag.ingest.chunk import build_chunks
from app.rag.ingest.embed import embed_texts
from app.rag.ingest.index import upsert_chunks

ROOT = Path(".")
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def _filter_sections(section_path: str, prefixes: List[str]) -> bool:
    sp = (section_path or "").strip().lower()
    return any(sp.startswith(p.strip().lower()) for p in prefixes)


def ingest_destination(
    dest: str,
    *,
    sections: Optional[List[str]] = None,
    max_chunks: int = 25,
    target_tokens: int = 550,
    max_tokens: int = 850,
    overlap_tokens: int = 0,
) -> None:
    raw = fetch_wikivoyage_parse_html(dest)
    raw_path = save_raw_page(raw, RAW_DIR)
    processed_path = clean_raw_file(raw_path, PROCESSED_DIR)

    chunks = build_chunks(
        processed_path,
        target_tokens=target_tokens,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
    )

    # Keep only selected sections (optional)
    if sections:
        chunks = [c for c in chunks if _filter_sections(c.section_path, sections)]

    # Keep only first N chunks (small-data mode)
    if max_chunks > 0:
        chunks = chunks[:max_chunks]

    if not chunks:
        raise RuntimeError("No chunks produced. Try different --sections or increase --max-chunks.")

    texts = [c.text for c in chunks]

    print(f"[INFO] {dest}: embedding {len(texts)} chunks (small-data mode)")

    doc_embeddings = embed_texts(
        texts,
        model=settings.gemini_embed_model,
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=768,
    )

    ids = [c.chunk_id for c in chunks]
    metadatas = [
        {
            "page_title": c.page_title,
            "section_path": c.section_path,
            "source_url": c.permalink_url or c.source_url,
            "attribution": c.attribution,
        }
        for c in chunks
    ]

    upsert_chunks(
        chroma_path=settings.chroma_dir,
        collection_name=settings.chroma_collection,
        ids=ids,
        documents=texts,
        embeddings=doc_embeddings,
        metadatas=metadatas,
    )

    print(f"[OK] {dest}: {len(chunks)} chunks indexed into {settings.chroma_collection}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destinations", nargs="+", required=True)

    # Small-data controls
    parser.add_argument("--sections", nargs="*", default=None, help="Only embed sections that start with these prefixes")
    parser.add_argument("--max-chunks", type=int, default=25)
    parser.add_argument("--target-tokens", type=int, default=550)
    parser.add_argument("--max-tokens", type=int, default=850)
    parser.add_argument("--overlap-tokens", type=int, default=0)

    args = parser.parse_args()

    for d in args.destinations:
        ingest_destination(
            d,
            sections=args.sections,
            max_chunks=args.max_chunks,
            target_tokens=args.target_tokens,
            max_tokens=args.max_tokens,
            overlap_tokens=args.overlap_tokens,
        )


if __name__ == "__main__":
    main()
