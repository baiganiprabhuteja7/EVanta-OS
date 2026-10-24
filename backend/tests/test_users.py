import uuid


def test_users_permissions_and_profiles(client):
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@evanta.os", "password": "Admin@123456"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    # Register standard user
    driver_email = f"driver_{uuid.uuid4().hex[:6]}@evanta.os"
    driver_reg = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Demo Driver",
            "email": driver_email,
            "password": "Password123!",
            "role": "user",
        },
    )
    assert driver_reg.status_code == 201
    driver_token = driver_reg.json()["access_token"]
    driver_id = driver_reg.json()["user_id"]

    # 1. Regular user gets own profile
    me_res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {driver_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == driver_email

    # 2. Regular user updates own profile
    patch_me = client.patch(
        "/api/v1/users/me",
        json={"full_name": "Demo Driver Updated"},
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert patch_me.status_code == 200
    assert patch_me.json()["full_name"] == "Demo Driver Updated"

    # 3. Regular user tries admin endpoint /api/v1/users -> Expect 403 Forbidden
    forbidden_list = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert forbidden_list.status_code == 403

    # 4. Admin accesses /api/v1/users -> Expect 200 OK
    admin_list = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_list.status_code == 200
    users_list = admin_list.json()
    assert any(u["email"] == driver_email for u in users_list)

    # 5. Admin updates driver status
    status_patch = client.patch(
        f"/api/v1/users/{driver_id}/status",
        json={"is_active": True, "role": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert status_patch.status_code == 200
    assert status_patch.json()["role"] == "admin"
