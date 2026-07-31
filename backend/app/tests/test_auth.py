import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_register_user_success():
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "role": "developer"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["role"] == "developer"
    assert data["is_active"] is True
    assert data["id"]
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_register_duplicate_email():
    email = f"duplicate-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "role": "developer"
        }
    )
    assert response.status_code == 201

    response2 = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "role": "developer"
        }
    )
    assert response2.status_code == 400
    assert response2.json()["detail"] == "A user with this email address already exists."


def test_login_returns_jwt():
    email = f"login-{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123"
    register_response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={
            "email": email,
            "password": password,
            "role": "developer"
        }
    )
    assert register_response.status_code == 201

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
