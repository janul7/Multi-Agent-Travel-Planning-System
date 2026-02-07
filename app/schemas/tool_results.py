from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class ToolResultEnvelope(BaseModel):
    status: Literal["ok", "error"]
    provider: str
    retrieved_at_utc: datetime = Field(description="UTC timestamp")
    cache_hit: bool = False
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class WeatherResult(BaseModel):
    summary: str
    high_c: float | None = None
    low_c: float | None = None


class CurrencyResult(BaseModel):
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)
    amount: float = Field(gt=0)
    converted_amount: float = Field(gt=0)
    fx_rate: float = Field(gt=0)


class EventsResult(BaseModel):
    city: str
    events: list[dict] = Field(default_factory=list, description="Keep simple first; tighten later")


class RAGChunk(BaseModel):
    text: str = Field(min_length=1)
    source_url: str
    title: str | None = None
    score: float = Field(ge=0, le=1)
