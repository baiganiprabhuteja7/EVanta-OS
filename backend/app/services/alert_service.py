from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alert
from app.models.charger import Charger
from app.models.station import Station


class AlertService:
    @staticmethod
    def get_alerts(db: Session, active_only: bool = False) -> List[dict]:
        """Returns alerts strictly for Prabhu's Grid."""
        station = db.scalar(select(Station).where(Station.station_code == settings.STATION_CODE))
        if not station:
            return []

        query = select(Alert).where(Alert.station_id == station.id).order_by(Alert.created_at.desc())
        if active_only:
            query = query.where(Alert.is_active == True)

        alerts = db.scalars(query).all()
        results = []
        for al in alerts:
            charger_code = None
            if al.charger_id:
                ch = db.scalar(select(Charger.charger_code).where(Charger.id == al.charger_id))
                charger_code = ch

            results.append({
                "id": al.id,
                "station_id": al.station_id,
                "charger_id": al.charger_id,
                "charger_code": charger_code,
                "severity": al.severity,
                "code": al.code,
                "title": al.title,
                "message": al.message,
                "is_active": al.is_active,
                "data_source": settings.DATA_SOURCE_LABEL,
                "created_at": al.created_at,
                "resolved_at": al.resolved_at,
            })
        return results

    @staticmethod
    def resolve_alert(db: Session, alert_id: int) -> dict:
        """Dismisses or resolves an alert."""
        station = db.scalar(select(Station).where(Station.station_code == settings.STATION_CODE))
        alert = db.scalar(
            select(Alert)
            .where(Alert.id == alert_id)
            .where(Alert.station_id == station.id)
        )
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert #{alert_id} not found at Prabhu's Grid.",
            )

        alert.is_active = False
        alert.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
        return {
            "id": alert.id,
            "status": "resolved",
            "message": f"Alert '{alert.title}' acknowledged and marked resolved.",
        }
