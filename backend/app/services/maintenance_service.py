from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.charger import Charger
from app.models.maintenance import MaintenanceRecord
from app.models.station import Station
from app.schemas.maintenance import MaintenanceRecordCreate, MaintenanceRecordUpdate


class MaintenanceService:
    @staticmethod
    def _enrich_record(rec: MaintenanceRecord, db: Session) -> dict:
        station = db.scalar(select(Station).where(Station.id == rec.station_id))
        charger = db.scalar(select(Charger).where(Charger.id == rec.charger_id)) if rec.charger_id else None

        return {
            "id": rec.id,
            "station_id": rec.station_id,
            "station_name": station.station_name if station else "Unknown Station",
            "charger_id": rec.charger_id,
            "charger_code": charger.charger_code if charger else None,
            "equipment_name": rec.equipment_name,
            "issue_description": rec.issue_description,
            "severity": rec.severity,
            "status": rec.status,
            "scheduled_date": rec.scheduled_date,
            "completed_date": rec.completed_date,
            "cost": float(rec.cost or 0.0),
            "technician_name": rec.technician_name,
            "resolution_notes": rec.resolution_notes,
            "created_by": rec.created_by,
            "created_at": rec.created_at,
            "updated_at": rec.updated_at,
        }

    @staticmethod
    def get_records(
        db: Session,
        station_id: Optional[int] = None,
        charger_id: Optional[int] = None,
        status_filter: Optional[str] = None,
    ) -> List[dict]:
        query = select(MaintenanceRecord).order_by(MaintenanceRecord.created_at.desc())

        if station_id:
            query = query.where(MaintenanceRecord.station_id == station_id)
        if charger_id:
            query = query.where(MaintenanceRecord.charger_id == charger_id)
        if status_filter and status_filter.lower() not in ["all", "all statuses"]:
            query = query.where(MaintenanceRecord.status.ilike(status_filter))

        records = db.scalars(query).all()
        return [MaintenanceService._enrich_record(r, db) for r in records]

    @staticmethod
    def get_record(db: Session, record_id: int) -> dict:
        rec = db.scalar(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
        if not rec:
            raise HTTPException(status_code=404, detail=f"Maintenance record {record_id} not found.")
        return MaintenanceService._enrich_record(rec, db)

    @staticmethod
    def create_record(db: Session, data: MaintenanceRecordCreate, user_id: Optional[int] = None) -> dict:
        station = db.scalar(select(Station).where(Station.id == data.station_id))
        if not station:
            raise HTTPException(status_code=404, detail=f"Station with ID {data.station_id} not found.")

        if data.charger_id:
            charger = db.scalar(select(Charger).where(Charger.id == data.charger_id))
            if not charger:
                raise HTTPException(status_code=404, detail=f"Charger with ID {data.charger_id} not found.")
            # If critical or high issue on charger, update charger status to Faulted
            if data.severity in ["High", "Critical"] and data.status in ["Reported", "In Progress"]:
                charger.status = "Faulted"

        new_rec = MaintenanceRecord(
            station_id=data.station_id,
            charger_id=data.charger_id,
            equipment_name=data.equipment_name.strip(),
            issue_description=data.issue_description.strip(),
            severity=data.severity,
            status=data.status,
            scheduled_date=data.scheduled_date,
            completed_date=data.completed_date,
            cost=data.cost,
            technician_name=data.technician_name,
            resolution_notes=data.resolution_notes,
            created_by=user_id,
        )
        db.add(new_rec)

        # Create alert if critical
        if data.severity in ["High", "Critical"]:
            alert = Alert(
                station_id=data.station_id,
                charger_id=data.charger_id,
                severity="critical" if data.severity == "Critical" else "warning",
                code="MAINT_REQ",
                title=f"Maintenance Required: {data.equipment_name}",
                message=f"Equipment issue reported: {data.issue_description}",
                is_active=True,
            )
            db.add(alert)

        db.commit()
        db.refresh(new_rec)
        return MaintenanceService._enrich_record(new_rec, db)

    @staticmethod
    def update_record(db: Session, record_id: int, data: MaintenanceRecordUpdate) -> dict:
        rec = db.scalar(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
        if not rec:
            raise HTTPException(status_code=404, detail=f"Maintenance record {record_id} not found.")

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            if hasattr(rec, key) and val is not None:
                setattr(rec, key, val)

        if data.status == "Completed" and not rec.completed_date:
            rec.completed_date = datetime.now(timezone.utc)
            # If charger was faulted, restore to Available
            if rec.charger_id:
                charger = db.scalar(select(Charger).where(Charger.id == rec.charger_id))
                if charger and charger.status == "Faulted":
                    charger.status = "Available"

        db.commit()
        db.refresh(rec)
        return MaintenanceService._enrich_record(rec, db)

    @staticmethod
    def delete_record(db: Session, record_id: int) -> dict:
        rec = db.scalar(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
        if not rec:
            raise HTTPException(status_code=404, detail=f"Maintenance record {record_id} not found.")
        db.delete(rec)
        db.commit()
        return {"status": "ok", "message": f"Maintenance record {record_id} deleted."}
