# app/rag/ingest/embed.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np
from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.core.config import settings


def _l2_normalize(v: List[float]) -> List[float]:
    arr = np.array(v, dtype=np.float32)
    n = np.linalg.norm(arr)
    if n == 0:
        return v
    return (arr / n).astype(np.float32).tolist()


def _approx_tokens(text: str) -> int:
    # Rough heuristic: ~4 chars/token (good enough to throttle)
    return max(1, len(text) // 4)


def _batch_by_token_budget(texts: Sequence[str], *, max_batch_tokens: int) -> Iterable[List[str]]:
    batch: List[str] = []
    running = 0
    for t in texts:
        tok = _approx_tokens(t)
        if batch and (running + tok) > max_batch_tokens:
            yield batch
            batch = [t]
            running = tok
        else:
            batch.append(t)
            running += tok
    if batch:
        yield batch


@dataclass
class _RateWindow:
    start: float
    used_tokens: int
    used_reqs: int


# Defaults tuned for free tier headroom (you can override via env if you add fields)
# Gemini rate limits are enforced by RPM/TPM/RPD. Exceeding any causes 429. :contentReference[oaicite:4]{index=4}
MAX_TPM = 25000   # below 30K to leave headroom
MAX_RPM = 80      # below 100 to leave headroom
MAX_BATCH_TOKENS = 9000  # <= ~3 batches/minute without exceeding TPM

_window = _RateWindow(start=time.monotonic(), used_tokens=0, used_reqs=0)


def _sleep_until_new_window():
    now = time.monotonic()
    elapsed = now - _window.start
    sleep_s = max(0.0, 60.0 - elapsed) + 1.0  # +1s safety buffer
    time.sleep(sleep_s)
    _window.start = time.monotonic()
    _window.used_tokens = 0
    _window.used_reqs = 0


def _throttle(next_tokens: int, next_reqs: int = 1):
    while True:
        now = time.monotonic()
        elapsed = now - _window.start
        if elapsed >= 60.0:
            _window.start = now
            _window.used_tokens = 0
            _window.used_reqs = 0

        if (_window.used_tokens + next_tokens) <= MAX_TPM and (_window.used_reqs + next_reqs) <= MAX_RPM:
            return

        _sleep_until_new_window()


def embed_texts(
    texts: Sequence[str],
    *,
    model: str = "gemini-embedding-001",
    task_type: str = "RETRIEVAL_DOCUMENT",
    output_dimensionality: int = 768,
) -> List[List[float]]:
    """
    Embeds texts with throttling to avoid 429 rate-limit errors.

    Notes:
    - gemini-embedding-001 input token limit is 2,048 per text. :contentReference[oaicite:5]{index=5}
    - For smaller dims (e.g. 768/1536), normalize embeddings. :contentReference[oaicite:6]{index=6}
    """
    client = genai.Client(api_key=settings.effective_api_key) if settings.effective_api_key else genai.Client()

    cfg = types.EmbedContentConfig(
        task_type=task_type,
        output_dimensionality=output_dimensionality,
    )

    out: List[List[float]] = []

    for batch in _batch_by_token_budget(texts, max_batch_tokens=MAX_BATCH_TOKENS):
        batch_tokens = sum(_approx_tokens(t) for t in batch)
        _throttle(batch_tokens, 1)

        # retry a couple times if server still says 429 (approx tokens can undercount)
        for attempt in range(3):
            try:
                res = client.models.embed_content(model=model, contents=batch, config=cfg)
                break
            except ClientError as e:
                # Handle rate limit
                if getattr(e, "status_code", None) == 429:
                    _sleep_until_new_window()
                    continue
                raise
        else:
            raise RuntimeError("Embedding failed after retries due to repeated 429 rate limits.")

        for emb in res.embeddings:
            vec = list(emb.values)
            # Normalize for 768/1536 (and generally any non-3072) as Google recommends. :contentReference[oaicite:7]{index=7}
            if output_dimensionality != 3072:
                vec = _l2_normalize(vec)
            out.append(vec)

        _window.used_tokens += batch_tokens
        _window.used_reqs += 1

    return out
