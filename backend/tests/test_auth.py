from datetime import datetime, timedelta, timezone
import uuid
import jwt
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.models.user import User


def test_health_check(client):
    """Health check remains open for monitoring."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["application"] == "Evanta OS"


def test_successful_login_with_email_and_username(client):
    """Test login via email and via username."""
    db = SessionLocal()
    unique_id = uuid.uuid4().hex[:8]
    email = f"official_{unique_id}@evanta.os"
    username = f"official_{unique_id}"
    raw_password = "SecurePassword123!"

    user = User(
        full_name="Officer Ramesh",
        email=email,
        username=username,
        password_hash=hash_password(raw_password),
        role="manager",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()

    # 1. Login using Email
    res_email = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": raw_password},
    )
    assert res_email.status_code == 200
    data_email = res_email.json()
    assert "access_token" in data_email
    assert data_email["token_type"] == "bearer"
    assert data_email["role"] == "manager"
    assert data_email["email"] == email

    # 2. Login using Username
    res_user = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": raw_password},
    )
    assert res_user.status_code == 200
    assert "access_token" in res_user.json()

    # 3. Form-urlencoded login (OAuth2 standard)
    res_form = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": raw_password},
    )
    assert res_form.status_code == 200


def test_invalid_credentials_returns_safe_error(client):
    """Ensures credential enumeration is prevented by generic safe errors."""
    # Non-existent user
    res_nonexistent = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@evanta.os", "password": "AnyPassword123!"},
    )
    assert res_nonexistent.status_code == 401
    assert "Invalid email/username or password." in res_nonexistent.json()["detail"]

    # Wrong password for existing user
    db = SessionLocal()
    email = f"valid_{uuid.uuid4().hex[:8]}@evanta.os"
    user = User(
        full_name="Valid Officer",
        email=email,
        password_hash=hash_password("RightPassword123!"),
        role="viewer",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()

    res_wrong_pw = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword999!"},
    )
    assert res_wrong_pw.status_code == 401
    assert "Invalid email/username or password." in res_wrong_pw.json()["detail"]


def test_login_throttling_and_lockout(client):
    """Repeated failed attempts lock account for 15 minutes."""
    db = SessionLocal()
    email = f"throttle_{uuid.uuid4().hex[:8]}@evanta.os"
    user = User(
        full_name="Throttle Test",
        email=email,
        password_hash=hash_password("RightPass123!"),
        role="viewer",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()

    # Attempt 5 consecutive wrong passwords
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "BadPassword"},
        )

    # 6th attempt should be blocked with 429 Too Many Requests
    lockout_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "BadPassword"},
    )
    assert lockout_res.status_code == 429
    assert "temporarily locked" in lockout_res.json()["detail"]


def test_inactive_account_rejection(client):
    """Deactivated accounts are rejected with 403 Forbidden."""
    db = SessionLocal()
    email = f"inactive_{uuid.uuid4().hex[:8]}@evanta.os"
    user = User(
        full_name="Deactivated Officer",
        email=email,
        password_hash=hash_password("Pass123!"),
        role="viewer",
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.close()

    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Pass123!"},
    )
    assert res.status_code == 403
    assert "deactivated" in res.json()["detail"].lower()


def test_logout_revokes_token(client):
    """Logout invalidates token, preventing further API access."""
    db = SessionLocal()
    email = f"logout_{uuid.uuid4().hex[:8]}@evanta.os"
    user = User(
        full_name="Logout User",
        email=email,
        password_hash=hash_password("Pass123!"),
        role="manager",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Pass123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify token works before logout
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200

    # Perform logout
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "ok"

    # Subsequent request using same token must be rejected with 401
    revoked_check = client.get("/api/v1/auth/me", headers=headers)
    assert revoked_check.status_code == 401
    assert "terminated" in revoked_check.json()["detail"].lower() or "invalid" in revoked_check.json()["detail"].lower()


def test_expired_or_invalid_tokens_rejected(client):
    """Tokens with invalid signatures or expired timestamps are rejected."""
    # 1. Invalid signature
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.tampered_signature"
    res1 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert res1.status_code == 401

    # 2. Expired token
    expired_payload = {
        "sub": "1",
        "role": "admin",
        "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
        "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    res2 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res2.status_code == 401


def test_password_reset_flow(client):
    """Test password reset request endpoint."""
    res = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": "official@evanta.os"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    # When email is unconfigured, message guides user to administrator
    if not settings.is_email_configured:
        assert data["email_configured"] is False
        assert "administrator" in data["message"].lower()


def test_dev_login_bypass_success(client):
    """Development admin bypass returns valid admin token that accesses protected endpoints."""
    settings.DEV_AUTH_BYPASS = True
    settings.ENVIRONMENT = "development"

    res = client.post("/api/v1/auth/dev-login")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    token = data["access_token"]

    # Verify that this development admin token can access protected administrator endpoints
    layout_res = client.get(
        "/api/v1/station/layout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert layout_res.status_code == 200
    assert layout_res.json()["station_id"] is not None


def test_dev_login_bypass_disabled_when_flag_false_or_in_production(client):
    """Development bypass is strictly rejected with 403 when disabled or in production."""
    # 1. Flag is False
    settings.DEV_AUTH_BYPASS = False
    settings.ENVIRONMENT = "development"
    res1 = client.post("/api/v1/auth/dev-login")
    assert res1.status_code == 403
    assert "disabled" in res1.json()["detail"].lower()

    # 2. Flag is True but Environment is Production
    settings.DEV_AUTH_BYPASS = True
    settings.ENVIRONMENT = "production"
    res2 = client.post("/api/v1/auth/dev-login")
    assert res2.status_code == 403
    assert "disabled" in res2.json()["detail"].lower()

    # Restore settings for subsequent tests
    settings.ENVIRONMENT = "development"
    settings.DEV_AUTH_BYPASS = True


def test_dev_status_endpoint(client):
    """Check dev status endpoint reports current bypass flag accurately."""
    settings.DEV_AUTH_BYPASS = True
    settings.ENVIRONMENT = "development"
    res = client.get("/api/v1/auth/dev-status")
    assert res.status_code == 200
    assert res.json()["dev_auth_bypass"] is True

