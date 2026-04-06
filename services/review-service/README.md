# Review Service

Review and rating service for restaurants and couriers in the Food Delivery platform.

Phase 8 status: completed in contract-stage.

## Scope

- Create/update/delete restaurant and courier reviews
- Validate that review author owns the order
- Validate that delivery is completed before review creation
- Calculate restaurant and courier rating summaries
- Publish `review-service.review.created` events

## API Endpoints

- `GET /health`
- `POST /api/v1/reviews`
- `GET /api/v1/reviews`
- `GET /api/v1/reviews/{review_id}`
- `PATCH /api/v1/reviews/{review_id}`
- `DELETE /api/v1/reviews/{review_id}`
- `GET /api/v1/reviews/restaurants/{restaurant_id}/rating`
- `GET /api/v1/reviews/couriers/{courier_id}/rating`

## Notes

- External access should go through `api-gateway`.
- Review validation uses direct internal HTTP calls to:
  - `order-service` for order ownership and restaurant id
  - `delivery-service` for delivery completion status and courier identity
- Review targets are modeled as `target_type + target_id` (`restaurant` / `courier`).
- Courier identity currently comes from `delivery-service` assignment contract; in local/dev
  flow it can be auto-selected from `DELIVERY_SERVICE_MOCK_COURIER_IDS`.

## Testing

```bash
make test-review
```
