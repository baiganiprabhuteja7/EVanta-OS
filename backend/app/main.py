from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database initial seed is run if empty
    seed_database()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="EV Charging Intelligence & Business Management Platform API",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware for React frontend integration
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
        "message": "Welcome to EVanta OS API",
        "status": "running",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": "EVanta OS",
        "version": settings.VERSION,
    }
