import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import init_db
from app.api.telemetry import router as telemetry_router
from app.api.events import router as events_router
from app.api.agent import router as agent_router
from app.api.demo import router as demo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AquaSentinel Cloud API: Real-Time IoT Water Telemetry Ingestion, "
        "Statistical Anomaly Detection, Sensor Health Isolation, and Agentic AI Investigation."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry_router)
app.include_router(events_router)
app.include_router(agent_router)
app.include_router(demo_router)


@app.get("/health", tags=["System"])
def root_health():
    return {
        "status": "HEALTHY",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "disclaimer": settings.SCIENTIFIC_DISCLAIMER,
    }


# Static frontend mounting if present
frontend_dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend_dist")
if os.path.exists(frontend_dist_path):
    assets_dir = os.path.join(frontend_dist_path, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(frontend_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "AquaSentinel API running on Render."}
