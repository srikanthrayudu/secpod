import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

pytestmark = pytest.mark.asyncio

async def test_register_user(client: AsyncClient):
    payload = {
        "email": "newuser@example.com",
        "password": "strongpassword123",
        "full_name": "New User"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert data["role"] == "admin"  # First user registered gets admin role in our service design fallback!

async def test_login_user(client: AsyncClient, test_user: User):
    # Form data request structure
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

async def test_login_invalid_password(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"}
    )
    assert response.status_code == 401

async def test_read_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

async def test_read_me_authorized(client: AsyncClient, test_user: User):
    # Obtain token
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"}
    )
    token = login_res.json()["access_token"]
    
    # Authorized Request
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
