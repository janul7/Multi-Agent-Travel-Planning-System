from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    page_title: str
    section_path: str
    source_url: str
    permalink_url: Optional[str]
    attribution: str
    text: str


def _stable_chunk_id(page_title: str, section_path: str, idx: int, text: str) -> str:
    h = hashlib.sha256()
    h.update(f"{page_title}|{section_path}|{idx}|".encode("utf-8"))
    h.update(text.encode("utf-8"))
    return h.hexdigest()


def _approx_tokens(text: str) -> int:
    # rough heuristic: ~4 chars/token for English-ish text
    return max(1, len(text) // 4)


def build_chunks(
    processed_json: Path,
    *,
    target_tokens: int = 650,
    max_tokens: int = 950,
    overlap_tokens: int = 120,
) -> List[Chunk]:
    """
    Token-ish chunking using cheap character heuristics.
    Keeps chunks well under embedding token limits for fast iteration.
    """
    doc = json.loads(processed_json.read_text(encoding="utf-8"))
    page_title = doc["page_title"]
    source_url = doc["source_url"]
    permalink_url = doc.get("permalink_url")
    attribution = f"Source: Wikivoyage (CC BY-SA 4.0), page: {page_title}"

    blocks = doc["blocks"]

    chunks: List[Chunk] = []
    cur_section: Optional[str] = None
    buf: List[str] = []
    buf_tokens = 0
    chunk_idx = 0

    def flush():
        nonlocal chunk_idx, buf, buf_tokens
        if not buf:
            return
        text = "\n\n".join(buf).strip()
        cid = _stable_chunk_id(page_title, cur_section or "Intro", chunk_idx, text)
        chunks.append(
            Chunk(
                chunk_id=cid,
                page_title=page_title,
                section_path=cur_section or "Intro",
                source_url=source_url,
                permalink_url=permalink_url,
                attribution=attribution,
                text=text,
            )
        )
        chunk_idx += 1

        # overlap: keep last overlap_tokens worth of lines
        if overlap_tokens > 0:
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            keep: List[str] = []
            running = 0
            for ln in reversed(lines):
                t = _approx_tokens(ln)
                if running + t > overlap_tokens:
                    break
                keep.append(ln)
                running += t
            keep.reverse()
            buf = ["\n".join(keep)] if keep else []
            buf_tokens = _approx_tokens("\n".join(buf)) if buf else 0
        else:
            buf = []
            buf_tokens = 0

    for b in blocks:
        section_path = b["section_path"]
        text = (b["text"] or "").strip()
        if not text:
            continue

        if cur_section is None:
            cur_section = section_path
        elif section_path != cur_section and buf:
            flush()
            cur_section = section_path

        t = _approx_tokens(text)

        if t > max_tokens:
            flush()
            cid = _stable_chunk_id(page_title, section_path, chunk_idx, text)
            chunks.append(
                Chunk(
                    chunk_id=cid,
                    page_title=page_title,
                    section_path=section_path,
                    source_url=source_url,
                    permalink_url=permalink_url,
                    attribution=attribution,
                    text=text,
                )
            )
            chunk_idx += 1
            continue

        if buf_tokens + t > max_tokens:
            flush()

        buf.append(text)
        buf_tokens += t

        if buf_tokens >= target_tokens:
            flush()

    flush()
    return chunks
