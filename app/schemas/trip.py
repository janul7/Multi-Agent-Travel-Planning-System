from __future__ import annotations

from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


class Money(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, description="ISO 4217 code, e.g. USD, SGD")


class TripRequest(BaseModel):
    destination: str = Field(min_length=2, description="City or country name, e.g. Singapore")
    start_date: date
    end_date: date

    pace: Literal["slow", "medium", "fast"] = "medium"
    interests: list[str] = Field(default_factory=list, description="e.g. food, museums, nature")
    constraints: list[str] = Field(default_factory=list, description="e.g. avoid long walking blocks")

    budget: Money | None = None
