"""Integration tests for menu item API endpoints."""

from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
import pytest

EXPECTED_MENU_ITEMS_COUNT = 2


async def _create_restaurant(client: AsyncClient) -> str:
    owner_id = str(uuid4())
    response = await client.post(
        "/api/v1/restaurants",
        json={
            "owner_id": owner_id,
            "name": "Test Restaurant",
            "description": "Test",
            "street": "123 Main St",
            "city": "New York",
            "postal_code": "10001",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "cuisine": "italian",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_create_and_get_menu_item_nested(restaurant_service_client: AsyncClient) -> None:
    """Test creating menu item via nested endpoint and retrieving by ID."""
    restaurant_id = await _create_restaurant(restaurant_service_client)

    menu_item_payload = {
        "name": "Margherita Pizza",
        "description": "Classic Italian pizza",
        "price_amount": "15.99",
        "category": "main_course",
        "image_url": "https://example.com/pizza.jpg",
    }

    create_response = await restaurant_service_client.post(
        f"/api/v1/restaurants/{restaurant_id}/menu-items",
        json=menu_item_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED

    menu_item = create_response.json()
    menu_item_id = menu_item["id"]
    assert menu_item["name"] == "Margherita Pizza"
    assert menu_item["price_amount"] == "15.99"
    assert menu_item["category"] == "main_course"
    assert menu_item["availability"] == "available"

    get_response = await restaurant_service_client.get(
        f"/api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}"
    )
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["id"] == menu_item_id


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_update_menu_item_nested_put(restaurant_service_client: AsyncClient) -> None:
    """Test updating a menu item via nested PUT endpoint."""
    restaurant_id = await _create_restaurant(restaurant_service_client)

    create_response = await restaurant_service_client.post(
        f"/api/v1/restaurants/{restaurant_id}/menu-items",
        json={
            "name": "Original Pizza",
            "description": "Original description",
            "price_amount": "10.00",
            "category": "appetizer",
        },
    )
    menu_item_id = create_response.json()["id"]

    update_payload = {
        "name": "Updated Pizza",
        "description": "Updated description",
        "price_amount": "12.50",
        "category": "main_course",
    }

    update_response = await restaurant_service_client.put(
        f"/api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}",
        json=update_payload,
    )
    assert update_response.status_code == status.HTTP_200_OK

    updated = update_response.json()
    assert updated["name"] == "Updated Pizza"
    assert updated["description"] == "Updated description"
    assert updated["price_amount"] == "12.50"
    assert updated["category"] == "main_course"


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_update_menu_item_availability(restaurant_service_client: AsyncClient) -> None:
    """Test updating menu item availability."""
    restaurant_id = await _create_restaurant(restaurant_service_client)

    create_response = await restaurant_service_client.post(
        f"/api/v1/restaurants/{restaurant_id}/menu-items",
        json={
            "name": "Pizza",
            "description": "Test",
            "price_amount": "15.99",
            "category": "main_course",
        },
    )
    menu_item_id = create_response.json()["id"]

    availability_response = await restaurant_service_client.patch(
        f"/api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}/availability",
        json={"availability": "out_of_stock"},
    )

    assert availability_response.status_code == status.HTTP_200_OK
    assert availability_response.json()["availability"] == "out_of_stock"


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_get_restaurant_menu_nested(restaurant_service_client: AsyncClient) -> None:
    """Test getting all menu items for a restaurant using nested menu endpoint."""
    restaurant_id = await _create_restaurant(restaurant_service_client)

    await restaurant_service_client.post(
        f"/api/v1/restaurants/{restaurant_id}/menu-items",
        json={
            "name": "Pizza",
            "description": "Test",
            "price_amount": "15.99",
            "category": "main_course",
        },
    )

    await restaurant_service_client.post(
        f"/api/v1/restaurants/{restaurant_id}/menu-items",
        json={
            "name": "Pasta",
            "description": "Test",
            "price_amount": "12.99",
            "category": "main_course",
        },
    )

    menu_response = await restaurant_service_client.get(f"/api/v1/restaurants/{restaurant_id}/menu")

    assert menu_response.status_code == status.HTTP_200_OK
    menu_items = menu_response.json()
    assert len(menu_items) == EXPECTED_MENU_ITEMS_COUNT
    names = {item["name"] for item in menu_items}
    assert names == {"Pizza", "Pasta"}


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_delete_menu_item_soft_delete(restaurant_service_client: AsyncClient) -> None:
    """Test deleting menu item marks it as discontinued."""
    restaurant_id = await _create_restaurant(restaurant_service_client)

    create_response = await restaurant_service_client.post(
        f"/api/v1/restaurants/{restaurant_id}/menu-items",
        json={
            "name": "Pizza",
            "description": "Test",
            "price_amount": "15.99",
            "category": "main_course",
        },
    )
    menu_item_id = create_response.json()["id"]

    delete_response = await restaurant_service_client.delete(
        f"/api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}"
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    get_response = await restaurant_service_client.get(
        f"/api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}"
    )
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["availability"] == "discontinued"


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_get_nonexistent_menu_item_returns_404(
    restaurant_service_client: AsyncClient,
) -> None:
    """Test getting nonexistent menu item returns 404."""
    restaurant_id = await _create_restaurant(restaurant_service_client)
    fake_id = str(uuid4())
    response = await restaurant_service_client.get(
        f"/api/v1/restaurants/{restaurant_id}/menu-items/{fake_id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "error" in response.json()
