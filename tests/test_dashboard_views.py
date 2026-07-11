import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

pytestmark = pytest.mark.asyncio

async def test_dashboard_index_unauthenticated(client: AsyncClient):
    """Unauthenticated access to dashboard redirects to login."""
    response = await client.get("/dashboard", headers={"accept": "text/html"})
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

async def test_dashboard_index_authenticated(client: AsyncClient, test_user: User):
    """Authenticated user can access dashboard."""
    # Login
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"}
    )
    assert login_res.status_code == 200
    # Access dashboard
    response = await client.get("/dashboard", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Dashboard" in response.text
    assert test_user.full_name in response.text

async def test_dashboard_users_unauthenticated(client: AsyncClient):
    """Unauthenticated access to /dashboard/users redirects to login."""
    response = await client.get("/dashboard/users", headers={"accept": "text/html"})
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

async def test_dashboard_users_non_admin(client: AsyncClient, test_user: User):
    """Non-admin user gets error page when accessing /dashboard/users."""
    # Login as regular user
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"}
    )
    assert login_res.status_code == 200
    response = await client.get("/dashboard/users", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "Only administrators can view this page." in response.text
    assert "error.html" in str(response.headers.get("content-type", "")) or "text/html" in response.headers["content-type"]

async def test_dashboard_users_admin(client: AsyncClient, test_admin: User):
    """Admin can access /dashboard/users."""
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_admin.email, "password": "password123"}
    )
    assert login_res.status_code == 200
    response = await client.get("/dashboard/users", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "User Management" in response.text
    assert test_admin.full_name in response.text

async def test_dashboard_profile_unauthenticated(client: AsyncClient):
    """Unauthenticated access to /dashboard/profile redirects to login."""
    response = await client.get("/dashboard/profile", headers={"accept": "text/html"})
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

async def test_dashboard_profile_authenticated(client: AsyncClient, test_user: User):
    """Authenticated user can access profile page."""
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"}
    )
    assert login_res.status_code == 200
    response = await client.get("/dashboard/profile", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "Profile" in response.text
    assert test_user.full_name in response.text

async def test_dashboard_profile_update(client: AsyncClient, test_user: User):
    """User can update their profile via POST."""
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"}
    )
    assert login_res.status_code == 200
    # Update profile
    response = await client.post(
        "/dashboard/profile",
        data={
            "full_name": "Updated Name",
            "bio": "New bio",
            "company": "Test Corp",
            "location": "Test City",
            "password": ""
        },
        headers={"accept": "text/html"}
    )
    assert response.status_code == 200
    # Should show success message
    assert "Profile updated successfully!" in response.text
    # Check that the updated name appears
    assert "Updated Name" in response.text

async def test_dashboard_users_htmx(client: AsyncClient, test_admin: User):
    """HTMX request to /dashboard/users returns partial table."""
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_admin.email, "password": "password123"}
    )
    assert login_res.status_code == 200
    response = await client.get(
        "/dashboard/users",
        headers={"hx-request": "true", "accept": "text/html"}
    )
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Should return the table partial, not full page
    assert "<table" in response.text
    assert "<!DOCTYPE html>" not in response.text  # partial does not include full HTML doc
    # Check for a known string in the table header
    assert "User Details" in response.text

async def test_dashboard_profile_update_htmx(client: AsyncClient, test_user: User):
    """HTMX profile update returns partial success."""
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"}
    )
    assert login_res.status_code == 200
    response = await client.post(
        "/dashboard/profile",
        data={
            "full_name": "HTMX Update",
            "bio": "",
            "company": "",
            "location": "",
            "password": ""
        },
        headers={"hx-request": "true", "accept": "text/html"}
    )
    assert response.status_code == 200
    assert "Profile updated successfully!" in response.text
    # Should return profile_card.html partial
    assert "profile-card-wrapper" in response.text
