import uuid
import pytest
from sqlalchemy import select

from app.cli.bootstrap_admin import bootstrap_admin
from app.core.security import verify_password
from app.db.session import SessionLocal
from app.models.user import User


def test_bootstrap_admin_cli_flow():
    """Test bootstrap CLI command creates first admin, hashes password, and refuses duplicate."""
    unique_suffix = uuid.uuid4().hex[:6]
    admin_email = f"bootadmin_{unique_suffix}@evanta.os"
    admin_user = f"bootadmin_{unique_suffix}"
    admin_password = "BootstrapPass123!"

    # 1. Force bootstrap of admin account
    success = bootstrap_admin(
        email=admin_email,
        username=admin_user,
        name="Bootstrap Administrator",
        password=admin_password,
        force=True,
    )
    assert success is True

    # 2. Verify account in database
    db = SessionLocal()
    user = db.scalar(select(User).where(User.email == admin_email))
    assert user is not None
    assert user.role == "admin"
    assert user.is_active is True
    assert user.password_hash != admin_password  # Must be hashed
    assert verify_password(admin_password, user.password_hash)  # Verified via Argon2
    db.close()

    # 3. Refuse second bootstrap when admin already exists without --force
    refusal = bootstrap_admin(
        email=f"another_{unique_suffix}@evanta.os",
        password="AnotherPassword123!",
        force=False,
    )
    assert refusal is False
