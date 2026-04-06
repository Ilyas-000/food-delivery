"""Integration tests for review API."""

from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
import pytest

TEST_USER_ID = "11111111-1111-1111-1111-111111111111"
TEST_RESTAURANT_ID = "22222222-2222-2222-2222-222222222222"
TEST_COURIER_ID = "44444444-4444-4444-4444-444444444444"
UPDATED_RATING = 4


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_create_list_update_delete_review(review_service_client: AsyncClient) -> None:
    """Exercise full CRUD flow for review endpoint."""
    order_id = str(uuid4())

    create_response = await review_service_client.post(
        "/api/v1/reviews",
        json={
            "order_id": order_id,
            "target_type": "restaurant",
            "target_id": TEST_RESTAURANT_ID,
            "rating": 5,
            "comment": "Excellent",
        },
        headers={"X-User-ID": TEST_USER_ID},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    review_id = create_response.json()["id"]

    list_response = await review_service_client.get(
        "/api/v1/reviews",
        params={"restaurant_id": TEST_RESTAURANT_ID},
    )
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.json()["total"] == 1

    update_response = await review_service_client.patch(
        f"/api/v1/reviews/{review_id}",
        json={"rating": 4, "comment": "Very good"},
        headers={"X-User-ID": TEST_USER_ID},
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["rating"] == UPDATED_RATING

    rating_response = await review_service_client.get(
        f"/api/v1/reviews/restaurants/{TEST_RESTAURANT_ID}/rating"
    )
    assert rating_response.status_code == status.HTTP_200_OK
    assert rating_response.json()["reviews_count"] == 1
    assert rating_response.json()["average_rating"] == "4.00"

    delete_response = await review_service_client.delete(
        f"/api/v1/reviews/{review_id}",
        headers={"X-User-ID": TEST_USER_ID},
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_create_review_requires_gateway_identity(review_service_client: AsyncClient) -> None:
    """Protected review creation should reject missing identity."""
    response = await review_service_client.post(
        "/api/v1/reviews",
        json={
            "order_id": str(uuid4()),
            "target_type": "restaurant",
            "target_id": TEST_RESTAURANT_ID,
            "rating": 5,
            "comment": "Excellent",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_create_and_rate_courier_review(review_service_client: AsyncClient) -> None:
    """Create courier review and fetch courier rating."""
    order_id = str(uuid4())

    create_response = await review_service_client.post(
        "/api/v1/reviews",
        json={
            "order_id": order_id,
            "target_type": "courier",
            "target_id": TEST_COURIER_ID,
            "rating": 5,
            "comment": "Fast courier",
        },
        headers={"X-User-ID": TEST_USER_ID},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.json()["target_type"] == "courier"

    rating_response = await review_service_client.get(
        f"/api/v1/reviews/couriers/{TEST_COURIER_ID}/rating"
    )
    assert rating_response.status_code == status.HTTP_200_OK
    assert rating_response.json()["reviews_count"] == 1
    assert rating_response.json()["average_rating"] == "5.00"
