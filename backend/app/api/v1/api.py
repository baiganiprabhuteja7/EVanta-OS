from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    analytics,
    auth,
    chargers,
    demo,
    expenses,
    maintenance,
    payments,
    sessions,
    settings,
    station,
    station_layout,
    stations,
    users,
)

api_router = APIRouter()

api_router.include_router(demo.router)
api_router.include_router(station.router)
api_router.include_router(station_layout.router)
api_router.include_router(alerts.router)
api_router.include_router(chargers.router)
api_router.include_router(sessions.router)
api_router.include_router(analytics.router)
api_router.include_router(settings.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(payments.router)
api_router.include_router(stations.router)
api_router.include_router(maintenance.router)
api_router.include_router(expenses.router)
