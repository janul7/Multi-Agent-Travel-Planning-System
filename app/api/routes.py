from fastapi import APIRouter

from datetime import datetime, timezone

from app.schemas.trip import TripRequest
from app.schemas.itinerary import ItineraryResponse, TripSummary, DayPlan, ScheduleItem
from app.schemas.tool_results import ToolResultEnvelope, WeatherResult

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/")
def root():
    return {"message": "Travel Buddy API is running"}

@router.post("/plan", response_model=ItineraryResponse)
def plan_trip(req: TripRequest) -> ItineraryResponse:
    # Temporary “mock” response to prove schemas work end-to-end
    weather_env = ToolResultEnvelope(
        status="ok",
        provider="mock",
        retrieved_at_utc=datetime.now(timezone.utc),
        cache_hit=True,
    )
    weather_data = WeatherResult(summary="Warm with possible showers", high_c=31, low_c=26)

    summary = TripSummary(
        destination=req.destination,
        date_range_local=f"{req.start_date} to {req.end_date}",
        pace=req.pace,
        constraints=req.constraints,
        budget_original=req.budget,
        budget_converted=None,
        budget_converted_data=None,
    )

    day1 = DayPlan(
        date=req.start_date,
        weather=weather_env,
        weather_data=weather_data,
        schedule=[ScheduleItem(time="09:30", title="Start with a nearby attraction", why="Easy first block")],
    )

    return ItineraryResponse(
        trip_request=req,
        trip_summary=summary,
        days=[day1],
        practical_notes=["This is a schema test response. Real agents will fill this later."],
        sources=[],
    )