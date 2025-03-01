"""Integration tests for user workflows."""

import pytest
from fastapi.testclient import TestClient

from ...database.models import User
from ...main import app
from ...services.auth_service import create_access_token

client = TestClient(app)


@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"sub": test_user["email"]})
    return {"Authorization": f"Bearer {token}"}


def test_user_signup_workflow(test_user):
    # 1. Register new user
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    assert "id" in response.json()
    user_id = response.json()["id"]

    # 2. Verify login works
    login_data = {"username": test_user["email"], "password": test_user["password"]}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()

    # 3. Get user profile
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user["email"]

    # 4. Update user profile
    update_data = {"full_name": "Updated Name"}
    response = client.patch(f"/users/{user_id}", headers=headers, json=update_data)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_password_reset_workflow(test_user, auth_headers):
    # 1. Request password reset
    response = client.post("/auth/forgot-password", json={"email": test_user["email"]})
    assert response.status_code == 200

    # 2. Get reset token from email (mocked in test environment)
    reset_token = (
        "test_reset_token"  # In real tests, get this from the test email service
    )

    # 3. Reset password
    new_password = "newpassword123"
    response = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": new_password},
    )
    assert response.status_code == 200

    # 4. Verify login works with new password
    login_data = {"username": test_user["email"], "password": new_password}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
