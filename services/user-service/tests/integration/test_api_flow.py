from fastapi import status
from httpx import AsyncClient
import pytest


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_register_login_profile_flow(user_service_client: AsyncClient) -> None:
    register_payload = {
        "email": "user@example.com",
        "password": "SecurePass123",
        "full_name": "John Doe",
    }
    register_response = await user_service_client.post(
        "/api/v1/auth/register",
        json=register_payload,
    )
    assert register_response.status_code == status.HTTP_201_CREATED

    login_response = await user_service_client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "SecurePass123"},
    )
    assert login_response.status_code == status.HTTP_200_OK
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    profile_response = await user_service_client.get("/api/v1/users/me", headers=headers)
    assert profile_response.status_code == status.HTTP_200_OK
    assert profile_response.json()["email"] == "user@example.com"

    update_response = await user_service_client.patch(
        "/api/v1/users/me",
        json={"full_name": "Jane Doe"},
        headers=headers,
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["full_name"] == "Jane Doe"


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_register_duplicate_email_conflict(user_service_client: AsyncClient) -> None:
    payload = {
        "email": "user@example.com",
        "password": "SecurePass123",
        "full_name": "John Doe",
    }
    first_response = await user_service_client.post("/api/v1/auth/register", json=payload)
    assert first_response.status_code == status.HTTP_201_CREATED

    second_response = await user_service_client.post("/api/v1/auth/register", json=payload)
    assert second_response.status_code == status.HTTP_409_CONFLICT
    assert "error" in second_response.json()
