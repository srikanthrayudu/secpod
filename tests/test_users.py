import pytest
from httpx import AsyncClient
from app.models.user import User

pytestmark = pytest.mark.asyncio

async def test_list_users_as_admin(client: AsyncClient, test_admin: User, test_user: User):
    # Log in as admin
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_admin.email, "password": "password123"}
    )
    token = login_res.json()["access_token"]
    
    # Fetch list
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

async def test_list_users_as_normal_user_denied(client: AsyncClient, test_user: User):
    # Log in as user
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"}
    )
    token = login_res.json()["access_token"]
    
    # Request denied
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 403
