from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure baseline database seed is run without hardcoding credentials
    try:
        seed_database()
    except Exception as e:
        print(f"[!] Warning: Initial database seed encountered an issue: {e}")
    yield


app = FastAPI(
    title="Evanta OS API",
    description="Evanta OS — EV Charging Station Monitoring & Management (Hyderabad, Telangana, India)",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware with explicit origins and credentialed request support
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Welcome to Evanta OS API",
        "station": settings.STATION_NAME,
        "location": "Hyderabad, Telangana, India",
        "status": "running",
        "data_mode": "DEMO / SIMULATED",
        "docs": "/docs",
    }


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": "Evanta OS",
        "station": settings.STATION_NAME,
        "location": "Hyderabad, Telangana, India",
        "data_mode": "DEMO MODE — SIMULATED DATA — NOT LIVE STATION TELEMETRY",
        "version": settings.VERSION,
    }
