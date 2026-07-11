import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

pytestmark = pytest.mark.asyncio

async def get_auth_headers(client: AsyncClient, user: User) -> dict:
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "password123"}
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

async def test_complete_qa_flow(client: AsyncClient, test_user: User, test_admin: User):
    user_headers = await get_auth_headers(client, test_user)
    admin_headers = await get_auth_headers(client, test_admin)

    # 1. Create a release
    release_payload = {
        "name": "v1.0.0",
        "target_date": "2026-12-31",
        "status": "planned"
    }
    res_release = await client.post("/api/v1/releases", json=release_payload, headers=admin_headers)
    assert res_release.status_code == 201
    release_data = res_release.json()
    release_id = release_data["id"]
    assert release_data["name"] == "v1.0.0"

    # 2. Create a test case
    test_case_payload = {
        "title": "Verify Login with Valid Credentials",
        "module": "Authentication",
        "priority": "critical",
        "steps": [
            "Navigate to login page.",
            "Input valid username and password.",
            "Click login."
        ],
        "expected_result": "User is redirected to the dashboard.",
        "tags": ["smoke", "auth"]
    }
    res_tc = await client.post("/api/v1/test-cases", json=test_case_payload, headers=user_headers)
    assert res_tc.status_code == 201
    tc_data = res_tc.json()
    tc_id = tc_data["id"]
    assert tc_data["title"] == "Verify Login with Valid Credentials"

    # 3. List test cases
    res_tc_list = await client.get("/api/v1/test-cases?module=Authentication", headers=user_headers)
    assert res_tc_list.status_code == 200
    assert len(res_tc_list.json()) >= 1

    # 4. Create a test run (passed)
    run_payload_passed = {
        "test_case_id": tc_id,
        "release_id": release_id,
        "status": "passed",
        "source": "manual",
        "duration_ms": 1200,
        "logs": "Steps executed successfully."
    }
    res_run_passed = await client.post("/api/v1/test-runs", json=run_payload_passed, headers=user_headers)
    assert res_run_passed.status_code == 201
    run_passed_data = res_run_passed.json()
    assert run_passed_data["status"] == "passed"

    # 5. Create a test run (failed) -> should automatically create a defect
    run_payload_failed = {
        "test_case_id": tc_id,
        "release_id": release_id,
        "status": "failed",
        "source": "automated",
        "duration_ms": 800,
        "logs": "AssertionError: Expected dashboard URL but got /error"
    }
    res_run_failed = await client.post("/api/v1/test-runs", json=run_payload_failed, headers=user_headers)
    assert res_run_failed.status_code == 201
    run_failed_data = res_run_failed.json()
    assert run_failed_data["status"] == "failed"

    # 6. Verify defect auto-creation
    res_defects = await client.get(f"/api/v1/defects?release_id={release_id}", headers=user_headers)
    assert res_defects.status_code == 200
    defects = res_defects.json()
    assert len(defects) >= 1
    assert "AssertionError" in defects[0]["description"]

    # 7. Check release readiness
    res_readiness = await client.get(f"/api/v1/releases/{release_id}/readiness", headers=user_headers)
    assert res_readiness.status_code == 200
    readiness = res_readiness.json()
    assert readiness["total_test_cases"] == 1
    assert readiness["executed_test_cases"] == 1
    assert readiness["coverage_percentage"] == 100.0
    assert readiness["pass_rate_percentage"] == 50.0  # 1 pass, 1 fail
    assert readiness["open_defects_count"] == 1

    # 8. Test AI drafting
    ai_draft_payload = {
        "requirement_text": "Citizen can report a streetlight issue with location and photo."
    }
    res_ai_draft = await client.post("/api/v1/ai/draft-test-case", json=ai_draft_payload, headers=user_headers)
    assert res_ai_draft.status_code == 200
    draft = res_ai_draft.json()
    assert "draft_steps" in draft
    assert len(draft["draft_steps"]) > 0
    assert "expected_result" in draft

    # 9. Test AI failure summarization
    ai_sum_payload = {
        "release_id": release_id,
        "limit": 10
    }
    res_ai_sum = await client.post("/api/v1/ai/summarize-failures", json=ai_sum_payload, headers=admin_headers)
    assert res_ai_sum.status_code == 200
    summary = res_ai_sum.json()
    assert "summary" in summary
    assert "themes" in summary
