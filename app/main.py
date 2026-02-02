from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Travel Buddy API")
app.include_router(router)
