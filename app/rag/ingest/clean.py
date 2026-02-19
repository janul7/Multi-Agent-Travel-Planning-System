from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class CleanBlock:
    section_path: str
    text: str


def _normalize_ws(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def html_to_blocks(html: str) -> List[CleanBlock]:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style"]):
        tag.decompose()

    for sel in [
        "span.mw-editsection",
        "sup.reference",
        "div#toc",
        "table",
        "div.navbox",
        "div.mw-references-wrap",
    ]:
        for t in soup.select(sel):
            t.decompose()

    root = soup.select_one("div.mw-parser-output") or soup

    blocks: List[CleanBlock] = []
    h2: Optional[str] = None
    h3: Optional[str] = None

    for el in root.find_all(["h2", "h3", "p", "ul", "ol"], recursive=True):
        if el.name == "h2":
            h2 = _normalize_ws(el.get_text(" ", strip=True))
            h3 = None
            continue
        if el.name == "h3":
            h3 = _normalize_ws(el.get_text(" ", strip=True))
            continue

        if el.name == "p":
            text = _normalize_ws(el.get_text(" ", strip=True))
            if len(text) < 40:
                continue
        else:
            items = [li.get_text(" ", strip=True) for li in el.find_all("li", recursive=False)]
            items = [_normalize_ws(x) for x in items if len(_normalize_ws(x)) >= 20]
            if not items:
                continue
            text = _normalize_ws("\n".join(f"- {x}" for x in items))

        section_parts = [p for p in [h2, h3] if p]
        section_path = " > ".join(section_parts) if section_parts else "Intro"
        blocks.append(CleanBlock(section_path=section_path, text=text))

    return blocks


def clean_raw_file(raw_path: Path, processed_dir: Path) -> Path:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    blocks = html_to_blocks(raw["html"])

    doc = {
        "page_title": raw["resolved_title"],
        "source_url": raw["source_url"],
        "permalink_url": raw.get("permalink_url"),
        "revid": raw.get("revid"),
        "fetched_at": raw.get("fetched_at"),
        "blocks": [{"section_path": b.section_path, "text": b.text} for b in blocks],
    }

    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / raw_path.name
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
