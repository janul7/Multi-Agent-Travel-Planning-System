# app/core/config.py
from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # project root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Mode flags
    offline_demo: bool = Field(default=False, alias="OFFLINE_DEMO")
    free_online: bool = Field(default=True, alias="FREE_ONLINE")
    events_on: bool = Field(default=False, alias="EVENTS_ON")

    # Gemini
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    gemini_embed_model: str = Field(default="gemini-embedding-001", alias="GEMINI_EMBED_MODEL")

    # RAG / Chroma
    chroma_dir: Path = Field(default=BASE_DIR / "data" / "chroma", alias="CHROMA_DIR")
    chroma_collection: str = Field(default="wikivoyage_chunks", alias="CHROMA_COLLECTION")

    # Weather
    openweather_api_key: str | None = Field(default=None, alias="OPENWEATHER_API_KEY")
    weather_units: str = Field(default="metric", alias="WEATHER_UNITS")

    # Currency
    exchangerate_api_key: str | None = Field(default=None, alias="EXCHANGERATE_API_KEY")

    # Events
    ticketmaster_api_key: str | None = Field(default=None, alias="TICKETMASTER_API_KEY")

    # Observability
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def effective_api_key(self) -> str | None:
        # If both exist, GOOGLE_API_KEY takes precedence in Google SDKs :contentReference[oaicite:3]{index=3}
        return self.google_api_key or self.gemini_api_key


settings = Settings()
