import uuid
import pytest


def test_users_authorization_and_rbac(client, admin_headers, manager_headers, viewer_headers):
    """Test user administration access restrictions by role."""
    # 1. Unauthenticated request to /users must return 401
    unauth_res = client.get("/api/v1/users")
    assert unauth_res.status_code == 401

    # 2. Manager calling /users must return 403 Forbidden
    manager_res = client.get("/api/v1/users", headers=manager_headers)
    assert manager_res.status_code == 403

    # 3. Read-Only official calling /users must return 403 Forbidden
    viewer_res = client.get("/api/v1/users", headers=viewer_headers)
    assert viewer_res.status_code == 403

    # 4. Administrator calling /users must succeed with 200
    admin_res = client.get("/api/v1/users", headers=admin_headers)
    assert admin_res.status_code == 200
    assert isinstance(admin_res.json(), list)


def test_admin_create_and_manage_authorized_users(client, admin_headers):
    """Administrator creates, deactivates, updates role, and deletes a user."""
    unique_suffix = uuid.uuid4().hex[:6]
    user_payload = {
        "full_name": "Station Tech Lead",
        "email": f"tech_{unique_suffix}@evanta.os",
        "username": f"tech_{unique_suffix}",
        "password": "TechPassword123!",
        "role": "manager",
        "is_active": True,
    }

    # 1. Create user
    create_res = client.post("/api/v1/users", json=user_payload, headers=admin_headers)
    assert create_res.status_code == 201
    created_user = create_res.json()
    assert created_user["email"] == user_payload["email"]
    assert created_user["role"] == "manager"
    user_id = created_user["id"]

    # 2. Deactivate user
    deact_res = client.patch(
        f"/api/v1/users/{user_id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False

    # Deactivated user cannot log in
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    assert login_res.status_code == 403

    # 3. Reactivate user and change role to viewer
    react_res = client.patch(
        f"/api/v1/users/{user_id}/status",
        json={"is_active": True, "role": "viewer"},
        headers=admin_headers,
    )
    assert react_res.status_code == 200
    assert react_res.json()["is_active"] is True
    assert react_res.json()["role"] == "viewer"

    # 4. Delete user
    del_res = client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "ok"
