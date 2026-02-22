"""Integration tests for restaurant API endpoints."""

from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
import pytest


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_create_and_get_restaurant(restaurant_service_client: AsyncClient) -> None:
    """Test creating and retrieving a restaurant."""
    owner_id = str(uuid4())
    create_payload = {
        "owner_id": owner_id,
        "name": "Test Restaurant",
        "description": "A wonderful test restaurant",
        "street": "123 Main St",
        "city": "New York",
        "postal_code": "10001",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "cuisine": "italian",
    }

    create_response = await restaurant_service_client.post(
        "/api/v1/restaurants",
        json=create_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED

    restaurant = create_response.json()
    restaurant_id = restaurant["id"]
    assert restaurant["name"] == "Test Restaurant"
    assert restaurant["cuisine"] == "italian"
    assert restaurant["is_active"] is True

    get_response = await restaurant_service_client.get(f"/api/v1/restaurants/{restaurant_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["id"] == restaurant_id


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_create_restaurant_duplicate_owner_and_name(
    restaurant_service_client: AsyncClient,
) -> None:
    """Test creating duplicate restaurant for same owner and name returns conflict."""
    owner_id = str(uuid4())
    payload = {
        "owner_id": owner_id,
        "name": "First Restaurant",
        "description": "Test",
        "street": "123 Main St",
        "city": "New York",
        "postal_code": "10001",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "cuisine": "italian",
    }

    first_response = await restaurant_service_client.post("/api/v1/restaurants", json=payload)
    assert first_response.status_code == status.HTTP_201_CREATED

    second_response = await restaurant_service_client.post("/api/v1/restaurants", json=payload)
    assert second_response.status_code == status.HTTP_409_CONFLICT
    assert "error" in second_response.json()


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_update_restaurant_with_put(restaurant_service_client: AsyncClient) -> None:
    """Test updating a restaurant with PUT."""
    owner_id = str(uuid4())
    create_payload = {
        "owner_id": owner_id,
        "name": "Original Name",
        "description": "Original description",
        "street": "123 Main St",
        "city": "New York",
        "postal_code": "10001",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "cuisine": "italian",
    }

    create_response = await restaurant_service_client.post(
        "/api/v1/restaurants",
        json=create_payload,
    )
    restaurant_id = create_response.json()["id"]

    update_payload = {
        "name": "Updated Name",
        "description": "Updated description",
        "cuisine": "chinese",
    }

    update_response = await restaurant_service_client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        json=update_payload,
    )
    assert update_response.status_code == status.HTTP_200_OK

    updated = update_response.json()
    assert updated["name"] == "Updated Name"
    assert updated["description"] == "Updated description"
    assert updated["cuisine"] == "chinese"


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_search_restaurants_by_cuisine(
    restaurant_service_client: AsyncClient,
) -> None:
    """Test searching restaurants by cuisine."""
    owner1 = str(uuid4())
    owner2 = str(uuid4())

    await restaurant_service_client.post(
        "/api/v1/restaurants",
        json={
            "owner_id": owner1,
            "name": "Italian Place",
            "description": "Test",
            "street": "123 Main St",
            "city": "New York",
            "postal_code": "10001",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "cuisine": "italian",
        },
    )

    await restaurant_service_client.post(
        "/api/v1/restaurants",
        json={
            "owner_id": owner2,
            "name": "Chinese Place",
            "description": "Test",
            "street": "456 Elm St",
            "city": "New York",
            "postal_code": "10002",
            "latitude": 40.7129,
            "longitude": -74.0061,
            "cuisine": "chinese",
        },
    )

    search_response = await restaurant_service_client.get(
        "/api/v1/restaurants",
        params={"cuisine": "italian"},
    )

    assert search_response.status_code == status.HTTP_200_OK
    results = search_response.json()
    assert len(results) == 1
    assert results[0]["cuisine"] == "italian"
    assert results[0]["name"] == "Italian Place"


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_delete_restaurant_soft_deletes(restaurant_service_client: AsyncClient) -> None:
    """Test deleting restaurant deactivates it."""
    owner_id = str(uuid4())
    create_response = await restaurant_service_client.post(
        "/api/v1/restaurants",
        json={
            "owner_id": owner_id,
            "name": "To Delete",
            "description": "Test",
            "street": "123 Main St",
            "city": "New York",
            "postal_code": "10001",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "cuisine": "italian",
        },
    )
    restaurant_id = create_response.json()["id"]

    delete_response = await restaurant_service_client.delete(f"/api/v1/restaurants/{restaurant_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    get_response = await restaurant_service_client.get(f"/api/v1/restaurants/{restaurant_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["is_active"] is False


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_get_nonexistent_restaurant_returns_404(
    restaurant_service_client: AsyncClient,
) -> None:
    """Test getting nonexistent restaurant returns 404."""
    fake_id = str(uuid4())
    response = await restaurant_service_client.get(f"/api/v1/restaurants/{fake_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "error" in response.json()
