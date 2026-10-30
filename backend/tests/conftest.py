import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def admin_headers():
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.role == "admin", User.is_active == True))
        if not admin:
            admin = User(
                full_name="Evanta Test Admin",
                email=f"admin_{uuid.uuid4().hex[:6]}@evanta.os",
                username=f"admin_{uuid.uuid4().hex[:6]}",
                password_hash=hash_password("AdminSecure2026!"),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        token = create_access_token(
            subject=admin.id,
            role=admin.role,
            full_name=admin.full_name,
            email=admin.email,
        )
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


@pytest.fixture(scope="function")
def manager_headers():
    db = SessionLocal()
    try:
        manager = User(
            full_name="Station Manager",
            email=f"manager_{uuid.uuid4().hex[:6]}@evanta.os",
            username=f"manager_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("ManagerSecure2026!"),
            role="manager",
            is_active=True,
        )
        db.add(manager)
        db.commit()
        db.refresh(manager)

        token = create_access_token(
            subject=manager.id,
            role=manager.role,
            full_name=manager.full_name,
            email=manager.email,
        )
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


@pytest.fixture(scope="function")
def viewer_headers():
    db = SessionLocal()
    try:
        viewer = User(
            full_name="Read-Only Official",
            email=f"viewer_{uuid.uuid4().hex[:6]}@evanta.os",
            username=f"viewer_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("ViewerSecure2026!"),
            role="viewer",
            is_active=True,
        )
        db.add(viewer)
        db.commit()
        db.refresh(viewer)

        token = create_access_token(
            subject=viewer.id,
            role=viewer.role,
            full_name=viewer.full_name,
            email=viewer.email,
        )
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()
