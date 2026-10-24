from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    auth,
    chargers,
    payments,
    sessions,
    settings,
    stations,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(stations.router)
api_router.include_router(chargers.router)
api_router.include_router(sessions.router)
api_router.include_router(payments.router)
api_router.include_router(analytics.router)
api_router.include_router(settings.router)
