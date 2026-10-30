from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.charger import Charger
from app.models.station import Station
from app.models.station_layout import StationLayout
from app.schemas.station_layout import LayoutAsset, LayoutData, StationBoundary, StationLayoutUpdate


def get_canonical_sample_layout(station_chargers: Optional[List[Charger]] = None) -> Dict[str, Any]:
    """
    Generate an illustrative sample 2D/3D station engineering layout for Hyderabad.
    Explicitly labeled: SAMPLE LAYOUT · ILLUSTRATIVE DIMENSIONS.
    """
    # Create lookup map for existing station chargers
    charger_map: Dict[str, Charger] = {}
    if station_chargers:
        for ch in station_chargers:
            charger_map[ch.charger_code] = ch

    assets: List[Dict[str, Any]] = [
        # --- INFRASTRUCTURE & ZONES ---
        {
            "id": "zone-entrance",
            "type": "entrance",
            "name": "Station Main Entry (Inbound Lane)",
            "x": 60,
            "y": 550,
            "width": 120,
            "height": 70,
            "rotation": 0,
            "charger_code": None,
            "metadata": {
                "lane_direction": "Inbound",
                "speed_limit_kmh": 10,
                "notes": "One-way entry lane with RFID barrier check",
            },
        },
        {
            "id": "zone-exit",
            "type": "exit",
            "name": "Station Exit (Outbound Lane)",
            "x": 820,
            "y": 550,
            "width": 120,
            "height": 70,
            "rotation": 0,
            "charger_code": None,
            "metadata": {
                "lane_direction": "Outbound",
                "speed_limit_kmh": 10,
                "notes": "Direct egress to Hyderabad station access road",
            },
        },
        {
            "id": "lane-circulation",
            "type": "lane",
            "name": "Internal Circulation Drive Aisle",
            "x": 200,
            "y": 340,
            "width": 600,
            "height": 80,
            "rotation": 0,
            "charger_code": None,
            "metadata": {
                "one_way": True,
                "surface": "High-durability tarmac",
            },
        },
        {
            "id": "util-substation-01",
            "type": "utility_room",
            "name": "Electrical Control & Switchgear Room",
            "x": 780,
            "y": 80,
            "width": 180,
            "height": 130,
            "rotation": 0,
            "charger_code": None,
            "metadata": {
                "access": "Authorized Personnel Only",
                "voltage_rating": "415V / 11kV step-down distribution",
                "fire_suppression": "Clean-agent system equipped",
            },
        },
        {
            "id": "tx-distribution-01",
            "type": "transformer",
            "name": "Primary 500kVA Distribution Transformer",
            "x": 630,
            "y": 85,
            "width": 120,
            "height": 110,
            "rotation": 0,
            "charger_code": None,
            "metadata": {
                "rating_kva": 500,
                "clearance_perimeter_m": 2.5,
                "oil_containment": "Compliant bund wall",
            },
        },
        {
            "id": "ped-canopy-walkway",
            "type": "pedestrian",
            "name": "Sheltered Pedestrian Access & Safety Zone",
            "x": 60,
            "y": 270,
            "width": 880,
            "height": 35,
            "rotation": 0,
            "charger_code": None,
            "metadata": {
                "anti_slip": True,
                "tactile_paving": True,
            },
        },
        {
            "id": "sign-totem-main",
            "type": "signage",
            "name": "Evanta OS Illuminated Pylon & Rate Display",
            "x": 30,
            "y": 600,
            "width": 40,
            "height": 40,
            "rotation": 0,
            "charger_code": None,
            "metadata": {
                "display": "Real-time tariff and bay availability",
                "lighting": "Low-power LED backlight",
            },
        },

        # --- AC CHARGING ZONE (WEST WING / NORTH CORRIDOR) ---
        # Bay 1 (AC)
        {
            "id": "bay-ac-01",
            "type": "parking_bay",
            "name": "Bay A1 (AC Standard 22kW)",
            "x": 80,
            "y": 140,
            "width": 100,
            "height": 110,
            "rotation": 0,
            "charger_code": "PRABHU-AC-01",
            "metadata": {
                "bay_code": "BAY-A1",
                "vehicle_type": "EV Car / SUV",
                "occupancy": "Occupied",
                "vehicle_model": "Tata Nexon EV",
            },
        },
        {
            "id": "chg-ac-01",
            "type": "charger_ac",
            "name": "AC Charger Pedestal 01 (22kW Type 2)",
            "x": 115,
            "y": 85,
            "width": 30,
            "height": 30,
            "rotation": 0,
            "charger_code": "PRABHU-AC-01",
            "metadata": {
                "charger_type": "AC",
                "connector_type": "Type 2",
                "rated_power_kw": 22.0,
                "status": charger_map.get("PRABHU-AC-01").status if "PRABHU-AC-01" in charger_map else "Charging",
                "cable_length_m": 5.0,
            },
        },

        # Bay 2 (AC)
        {
            "id": "bay-ac-02",
            "type": "parking_bay",
            "name": "Bay A2 (AC Standard 22kW)",
            "x": 200,
            "y": 140,
            "width": 100,
            "height": 110,
            "rotation": 0,
            "charger_code": "PRABHU-AC-02",
            "metadata": {
                "bay_code": "BAY-A2",
                "vehicle_type": "EV Car / SUV",
                "occupancy": "Available",
            },
        },
        {
            "id": "chg-ac-02",
            "type": "charger_ac",
            "name": "AC Charger Pedestal 02 (22kW Type 2)",
            "x": 235,
            "y": 85,
            "width": 30,
            "height": 30,
            "rotation": 0,
            "charger_code": "PRABHU-AC-02",
            "metadata": {
                "charger_type": "AC",
                "connector_type": "Type 2",
                "rated_power_kw": 22.0,
                "status": charger_map.get("PRABHU-AC-02").status if "PRABHU-AC-02" in charger_map else "Available",
                "cable_length_m": 5.0,
            },
        },

        # Bay 3 (AC)
        {
            "id": "bay-ac-03",
            "type": "parking_bay",
            "name": "Bay A3 (AC Standard 22kW)",
            "x": 320,
            "y": 140,
            "width": 100,
            "height": 110,
            "rotation": 0,
            "charger_code": "PRABHU-AC-03",
            "metadata": {
                "bay_code": "BAY-A3",
                "vehicle_type": "EV Car / SUV",
                "occupancy": "Available",
            },
        },
        {
            "id": "chg-ac-03",
            "type": "charger_ac",
            "name": "AC Charger Pedestal 03 (22kW Type 2)",
            "x": 355,
            "y": 85,
            "width": 30,
            "height": 30,
            "rotation": 0,
            "charger_code": "PRABHU-AC-03",
            "metadata": {
                "charger_type": "AC",
                "connector_type": "Type 2",
                "rated_power_kw": 22.0,
                "status": charger_map.get("PRABHU-AC-03").status if "PRABHU-AC-03" in charger_map else "Available",
                "cable_length_m": 5.0,
            },
        },

        # Bay 4 (AC)
        {
            "id": "bay-ac-04",
            "type": "parking_bay",
            "name": "Bay A4 (AC Standard 22kW)",
            "x": 440,
            "y": 140,
            "width": 100,
            "height": 110,
            "rotation": 0,
            "charger_code": "PRABHU-AC-04",
            "metadata": {
                "bay_code": "BAY-A4",
                "vehicle_type": "EV Car / Fleet",
                "occupancy": "Available",
            },
        },
        {
            "id": "chg-ac-04",
            "type": "charger_ac",
            "name": "AC Charger Pedestal 04 (22kW Type 2)",
            "x": 475,
            "y": 85,
            "width": 30,
            "height": 30,
            "rotation": 0,
            "charger_code": "PRABHU-AC-04",
            "metadata": {
                "charger_type": "AC",
                "connector_type": "Type 2",
                "rated_power_kw": 22.0,
                "status": charger_map.get("PRABHU-AC-04").status if "PRABHU-AC-04" in charger_map else "Available",
                "cable_length_m": 5.0,
            },
        },

        # --- DC FAST CHARGING ZONE (SOUTH WING / CORRIDOR) ---
        # Bay 1 (DC)
        {
            "id": "bay-dc-01",
            "type": "parking_bay",
            "name": "Bay D1 (DC Fast Charging 60kW)",
            "x": 200,
            "y": 440,
            "width": 110,
            "height": 120,
            "rotation": 0,
            "charger_code": "PRABHU-DC-01",
            "metadata": {
                "bay_code": "BAY-D1",
                "vehicle_type": "EV Commercial / SUV",
                "occupancy": "Occupied",
                "vehicle_model": "Hyundai Ioniq 5",
            },
        },
        {
            "id": "chg-dc-01",
            "type": "charger_dc",
            "name": "DC Fast Charger Kiosk 01 (60kW CCS2/CHAdeMO)",
            "x": 235,
            "y": 575,
            "width": 40,
            "height": 35,
            "rotation": 0,
            "charger_code": "PRABHU-DC-01",
            "metadata": {
                "charger_type": "DC",
                "connector_type": "CCS2 / CHAdeMO",
                "rated_power_kw": 60.0,
                "status": charger_map.get("PRABHU-DC-01").status if "PRABHU-DC-01" in charger_map else "Charging",
                "liquid_cooled_cable": False,
            },
        },

        # Bay 2 (DC)
        {
            "id": "bay-dc-02",
            "type": "parking_bay",
            "name": "Bay D2 (DC Ultra-Fast 120kW)",
            "x": 340,
            "y": 440,
            "width": 110,
            "height": 120,
            "rotation": 0,
            "charger_code": "PRABHU-DC-02",
            "metadata": {
                "bay_code": "BAY-D2",
                "vehicle_type": "EV Premium / Bus",
                "occupancy": "Available",
            },
        },
        {
            "id": "chg-dc-02",
            "type": "charger_dc",
            "name": "DC Ultra-Fast Kiosk 02 (120kW Dual CCS2)",
            "x": 375,
            "y": 575,
            "width": 40,
            "height": 35,
            "rotation": 0,
            "charger_code": "PRABHU-DC-02",
            "metadata": {
                "charger_type": "DC",
                "connector_type": "Dual CCS2",
                "rated_power_kw": 120.0,
                "status": charger_map.get("PRABHU-DC-02").status if "PRABHU-DC-02" in charger_map else "Available",
                "liquid_cooled_cable": True,
            },
        },

        # Bay 3 (DC)
        {
            "id": "bay-dc-03",
            "type": "parking_bay",
            "name": "Bay D3 (DC Ultra-Fast 120kW)",
            "x": 480,
            "y": 440,
            "width": 110,
            "height": 120,
            "rotation": 0,
            "charger_code": "PRABHU-DC-03",
            "metadata": {
                "bay_code": "BAY-D3",
                "vehicle_type": "EV Commercial / Luxury",
                "occupancy": "Available",
            },
        },
        {
            "id": "chg-dc-03",
            "type": "charger_dc",
            "name": "DC Ultra-Fast Kiosk 03 (120kW Dual CCS2)",
            "x": 515,
            "y": 575,
            "width": 40,
            "height": 35,
            "rotation": 0,
            "charger_code": "PRABHU-DC-03",
            "metadata": {
                "charger_type": "DC",
                "connector_type": "Dual CCS2",
                "rated_power_kw": 120.0,
                "status": charger_map.get("PRABHU-DC-03").status if "PRABHU-DC-03" in charger_map else "Available",
                "liquid_cooled_cable": True,
            },
        },

        # Bay 4 (DC)
        {
            "id": "bay-dc-04",
            "type": "parking_bay",
            "name": "Bay D4 (DC High-Power 150kW)",
            "x": 620,
            "y": 440,
            "width": 110,
            "height": 120,
            "rotation": 0,
            "charger_code": "PRABHU-DC-04",
            "metadata": {
                "bay_code": "BAY-D4",
                "vehicle_type": "Heavy Commercial / Fleet",
                "occupancy": "Occupied",
                "vehicle_model": "MG ZS EV",
            },
        },
        {
            "id": "chg-dc-04",
            "type": "charger_dc",
            "name": "DC High-Power Kiosk 04 (150kW Dual CCS2)",
            "x": 655,
            "y": 575,
            "width": 40,
            "height": 35,
            "rotation": 0,
            "charger_code": "PRABHU-DC-04",
            "metadata": {
                "charger_type": "DC",
                "connector_type": "Dual CCS2",
                "rated_power_kw": 150.0,
                "status": charger_map.get("PRABHU-DC-04").status if "PRABHU-DC-04" in charger_map else "Available",
                "liquid_cooled_cable": True,
            },
        },
    ]

    return {
        "boundary": {
            "width": 1000.0,
            "height": 650.0,
            "label": "Hyderabad Station Perimeter (PRABHU-HYD-01)",
        },
        "assets": assets,
    }


class StationLayoutService:
    @staticmethod
    def get_or_create_layout(db: Session, station_id: int, is_demo: bool = False) -> StationLayout:
        """
        Retrieve existing layout or seed the initial canonical sample layout.
        Enforces single station isolation for Hyderabad.
        """
        layout = db.scalar(
            select(StationLayout).where(
                StationLayout.station_id == station_id,
                StationLayout.is_demo == is_demo,
            )
        )

        if not layout:
            chargers = db.scalars(select(Charger).where(Charger.station_id == station_id)).all()
            sample_data = get_canonical_sample_layout(chargers)
            layout = StationLayout(
                station_id=station_id,
                name="Hyderabad Station Engineering Floor Plan",
                version=1,
                is_demo=is_demo,
                scale_ratio=1.0,
                scale_verified=False,
                disclaimer="SAMPLE LAYOUT · ILLUSTRATIVE DIMENSIONS · NOT SURVEYED HARDWARE TELEMETRY",
                layout_data=sample_data,
            )
            db.add(layout)
            db.commit()
            db.refresh(layout)

        # Merge live charger status into layout assets where matched
        chargers = db.scalars(select(Charger).where(Charger.station_id == station_id)).all()
        charger_lookup = {ch.charger_code: ch for ch in chargers}
        data = dict(layout.layout_data)
        updated = False
        for asset in data.get("assets", []):
            code = asset.get("charger_code")
            if code and code in charger_lookup:
                ch = charger_lookup[code]
                meta = asset.get("metadata", {})
                if meta.get("status") != ch.status or meta.get("rated_power_kw") != float(ch.rated_power_kw):
                    meta["status"] = ch.status
                    meta["rated_power_kw"] = float(ch.rated_power_kw)
                    meta["voltage"] = float(ch.voltage or 230.0)
                    meta["current_amp"] = float(ch.current_amp or 0.0)
                    asset["metadata"] = meta
                    updated = True

        if updated:
            layout.layout_data = data
            db.commit()
            db.refresh(layout)

        return layout

    @staticmethod
    def update_layout(
        db: Session,
        station_id: int,
        payload: StationLayoutUpdate,
        user_id: int,
        is_demo: bool = False,
    ) -> StationLayout:
        """
        Update layout geometry with optimistic concurrency protection.
        """
        layout = db.scalar(
            select(StationLayout).where(
                StationLayout.station_id == station_id,
                StationLayout.is_demo == is_demo,
            )
        )

        if not layout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station layout not found.",
            )

        # Optimistic concurrency check
        if layout.version != payload.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflict: Layout version mismatch (current: v{layout.version}, submitted: v{payload.version}). Reload to merge latest changes.",
            )

        # Basic geometry sanity validation
        if not payload.layout_data.assets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Station layout must contain at least one asset.",
            )

        for asset in payload.layout_data.assets:
            if asset.width <= 0 or asset.height <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Asset '{asset.name}' has invalid dimensions (width and height must be positive).",
                )
            if asset.x < 0 or asset.y < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Asset '{asset.name}' has out-of-bounds coordinates (x and y cannot be negative).",
                )

        if payload.name:
            layout.name = payload.name
        if payload.scale_ratio is not None:
            layout.scale_ratio = payload.scale_ratio
        if payload.scale_verified is not None:
            layout.scale_verified = payload.scale_verified
            if payload.scale_verified:
                layout.disclaimer = "VERIFIED SITE LAYOUT · REGISTERED SCALE"
            else:
                layout.disclaimer = "SAMPLE LAYOUT · ILLUSTRATIVE DIMENSIONS · NOT SURVEYED HARDWARE TELEMETRY"

        layout.layout_data = payload.layout_data.model_dump()
        layout.version += 1
        layout.created_by = user_id
        db.commit()
        db.refresh(layout)
        return layout

    @staticmethod
    def reset_layout(
        db: Session,
        station_id: int,
        user_id: int,
        is_demo: bool = False,
    ) -> StationLayout:
        """
        Reset layout back to the canonical sample layout with illustrative dimensions.
        """
        layout = db.scalar(
            select(StationLayout).where(
                StationLayout.station_id == station_id,
                StationLayout.is_demo == is_demo,
            )
        )

        chargers = db.scalars(select(Charger).where(Charger.station_id == station_id)).all()
        canonical = get_canonical_sample_layout(chargers)

        if not layout:
            layout = StationLayout(
                station_id=station_id,
                name="Hyderabad Station Engineering Floor Plan",
                version=1,
                is_demo=is_demo,
                scale_ratio=1.0,
                scale_verified=False,
                disclaimer="SAMPLE LAYOUT · ILLUSTRATIVE DIMENSIONS · NOT SURVEYED HARDWARE TELEMETRY",
                layout_data=canonical,
                created_by=user_id,
            )
            db.add(layout)
        else:
            layout.name = "Hyderabad Station Engineering Floor Plan"
            layout.version += 1
            layout.scale_ratio = 1.0
            layout.scale_verified = False
            layout.disclaimer = "SAMPLE LAYOUT · ILLUSTRATIVE DIMENSIONS · NOT SURVEYED HARDWARE TELEMETRY"
            layout.layout_data = canonical
            layout.created_by = user_id

        db.commit()
        db.refresh(layout)
        return layout
