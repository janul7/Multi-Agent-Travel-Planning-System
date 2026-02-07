import json
from pathlib import Path

from app.schemas.trip import TripRequest, Money
from app.schemas.tool_results import ToolResultEnvelope, WeatherResult, CurrencyResult, EventsResult, RAGChunk
from app.schemas.itinerary import ItineraryResponse

OUT_DIR = Path("docs/contracts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    Money,
    TripRequest,
    ToolResultEnvelope,
    WeatherResult,
    CurrencyResult,
    EventsResult,
    RAGChunk,
    ItineraryResponse,
]

for m in MODELS:
    schema = m.model_json_schema()
    (OUT_DIR / f"{m.__name__}.schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")

print(f"Wrote {len(MODELS)} schemas to {OUT_DIR}")
