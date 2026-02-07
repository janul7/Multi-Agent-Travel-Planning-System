from __future__ import annotations

from datetime import date
from pydantic import BaseModel, Field

from app.schemas.trip import TripRequest, Money
from app.schemas.tool_results import ToolResultEnvelope, WeatherResult, CurrencyResult, EventsResult, RAGChunk


class ScheduleItem(BaseModel):
    time: str = Field(description="Local time like 09:30")
    title: str
    why: str | None = None


class DayPlan(BaseModel):
    date: date
    weather: ToolResultEnvelope | None = None
    weather_data: WeatherResult | None = None
    schedule: list[ScheduleItem] = Field(default_factory=list)
    events: ToolResultEnvelope | None = None
    events_data: EventsResult | None = None


class TripSummary(BaseModel):
    destination: str
    date_range_local: str
    pace: str
    constraints: list[str] = Field(default_factory=list)
    budget_original: Money | None = None
    budget_converted: ToolResultEnvelope | None = None
    budget_converted_data: CurrencyResult | None = None


class ItineraryResponse(BaseModel):
    trip_request: TripRequest
    trip_summary: TripSummary
    days: list[DayPlan]
    practical_notes: list[str] = Field(default_factory=list)
    sources: list[RAGChunk] = Field(default_factory=list)
