import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_health_endpoint(client: AsyncClient):
    """Health endpoint returns 200 and expected JSON structure."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert data["status"] in {"ok", "degraded"}
    assert data["db"] in {"ok", "error"}
    assert data["ai_provider"] in {"ok", "error"}
    assert data["project"] == "QualityHub"
