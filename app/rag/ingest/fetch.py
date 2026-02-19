from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"
WIKIVOYAGE_PAGE_BASE = "https://en.wikivoyage.org/wiki/"


@dataclass(frozen=True)
class RawPage:
    requested_title: str
    resolved_title: str
    pageid: int
    revid: Optional[int]
    html: str
    fetched_at: str
    source_url: str
    permalink_url: Optional[str]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPError)),
)
def fetch_wikivoyage_parse_html(title: str, *, timeout_s: float = 30.0) -> RawPage:
    """
    Fetch rendered HTML via MediaWiki Action API (action=parse).
    This is much more stable than scraping full pages.
    """
    headers = {
        "User-Agent": "travel-buddy-rag/0.1 (contact: you@example.com) httpx",
        "Accept": "application/json",
    }

    params = {
        "action": "parse",
        "page": title,
        "prop": "text|displaytitle|revid",
        "format": "json",
        "formatversion": "2",
        "redirects": "1",
    }

    with httpx.Client(timeout=timeout_s, headers=headers) as client:
        r = client.get(WIKIVOYAGE_API, params=params)
        r.raise_for_status()
        data: Dict[str, Any] = r.json()

    if "error" in data:
        raise RuntimeError(f"MediaWiki API error for '{title}': {data['error']}")

    parsed = data["parse"]
    resolved_title = parsed.get("title") or title
    pageid = int(parsed["pageid"])
    revid = parsed.get("revid")
    html = parsed["text"]

    source_url = WIKIVOYAGE_PAGE_BASE + resolved_title.replace(" ", "_")
    permalink_url = None
    if revid:
        permalink_url = (
            "https://en.wikivoyage.org/w/index.php?title="
            f"{resolved_title.replace(' ', '_')}&oldid={revid}"
        )

    return RawPage(
        requested_title=title,
        resolved_title=resolved_title,
        pageid=pageid,
        revid=revid,
        html=html,
        fetched_at=_now_iso(),
        source_url=source_url,
        permalink_url=permalink_url,
    )


def save_raw_page(raw: RawPage, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = raw.resolved_title.replace("/", "_").replace(" ", "_")
    out_path = out_dir / f"{safe}.json"
    payload = {
        "requested_title": raw.requested_title,
        "resolved_title": raw.resolved_title,
        "pageid": raw.pageid,
        "revid": raw.revid,
        "fetched_at": raw.fetched_at,
        "source_url": raw.source_url,
        "permalink_url": raw.permalink_url,
        "html": raw.html,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
