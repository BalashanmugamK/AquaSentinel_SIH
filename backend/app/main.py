from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .config import get_settings
from .database import Base, engine
from .routers import events, readings, tools

settings = get_settings()

# Prototype-level: create tables on startup instead of running migrations.
# Fine for a 1-week build; swap for Alembic if the project continues.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AquaSentinel Backend",
    description="Workstream B — sensor ingestion, storage, anomaly events, and agent tools.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(readings.router)
app.include_router(events.router)
app.include_router(tools.router)


@app.get("/health")
def health():
    return {"status": "ok"}
