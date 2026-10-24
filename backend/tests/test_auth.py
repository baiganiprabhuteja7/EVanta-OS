import uuid


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_user_registration_and_login(client):
    random_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "full_name": "Test Driver",
        "email": random_email,
        "password": "Password123!",
        "role": "user",
    }
    # Register
    reg_response = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_response.status_code == 201
    data = reg_response.json()
    assert "access_token" in data
    assert data["email"] == random_email
    token = data["access_token"]

    # Duplicate registration should fail
    dup_response = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_response.status_code == 400

    # JSON Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": random_email, "password": "Password123!"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Form Login (OAuth2 standard)
    form_response = client.post(
        "/api/v1/auth/login",
        data={"username": random_email, "password": "Password123!"},
    )
    assert form_response.status_code == 200
    assert "access_token" in form_response.json()

    # Invalid password login
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": random_email, "password": "WrongPassword"},
    )
    assert bad_login.status_code == 401

    # /auth/me with Bearer token
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == random_email
    assert "password_hash" not in me_response.json()

    # /auth/logout
    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_response.status_code == 200
