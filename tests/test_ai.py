import pytest
from httpx import AsyncClient
from app.models.user import User

pytestmark = pytest.mark.asyncio

async def test_ai_draft_test_case(client: AsyncClient, test_user: User):
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"requirement_text": "User can export test cases to CSV for offline review."}
    response = await client.post("/api/v1/ai/draft-test-case", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "draft_steps" in data
    assert len(data["draft_steps"]) > 0
    assert "expected_result" in data

async def test_ai_draft_unauthorized(client: AsyncClient):
    payload = {"requirement_text": "Should fail"}
    response = await client.post("/api/v1/ai/draft-test-case", json=payload)
    assert response.status_code == 401
