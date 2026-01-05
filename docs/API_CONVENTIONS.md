# API Conventions

This document defines the API conventions and standards for all microservices in the Food Delivery platform.

## General Principles

1. **RESTful Design** - Follow REST principles
2. **Consistency** - Same patterns across all services
3. **Versioning** - All APIs versioned (v1, v2, etc.)
4. **JSON** - Default content type
5. **HTTPS** - In production (HTTP in development)

---

## URL Structure

### Base URL Pattern

```
http(s)://{host}:{port}/api/v{version}/{resource}
```

**Examples:**
```
http://localhost:8001/api/v1/users
http://localhost:8002/api/v1/restaurants
http://localhost:8003/api/v1/orders
```

### Resource Naming

- ✅ Use **plural nouns**: `/users`, `/orders`, `/restaurants`
- ✅ Use **kebab-case** for multi-word resources: `/menu-items`, `/delivery-addresses`
- ❌ Avoid verbs: `/getUser`, `/createOrder`
- ❌ Avoid uppercase: `/Users`, `/Orders`

### Nested Resources

Use nesting to show relationships (max 2 levels):

```
GET  /api/v1/restaurants/{id}/menu-items
GET  /api/v1/orders/{id}/items
POST /api/v1/users/{id}/addresses
```

For deep nesting, use query parameters instead:

```
✅ GET /api/v1/reviews?restaurant_id=123
❌ GET /api/v1/restaurants/123/reviews/456/comments
```

---

## HTTP Methods

| Method | Usage | Idempotent | Safe |
|--------|-------|------------|------|
| `GET` | Retrieve resource(s) | ✅ | ✅ |
| `POST` | Create new resource | ❌ | ❌ |
| `PUT` | Replace entire resource | ✅ | ❌ |
| `PATCH` | Partial update | ❌* | ❌ |
| `DELETE` | Remove resource | ✅ | ❌ |

*PATCH should be idempotent when possible

### Examples

```http
GET    /api/v1/users          # List users
GET    /api/v1/users/{id}     # Get specific user
POST   /api/v1/users          # Create user
PUT    /api/v1/users/{id}     # Replace user
PATCH  /api/v1/users/{id}     # Update user fields
DELETE /api/v1/users/{id}     # Delete user
```

---

## HTTP Status Codes

### Success (2xx)

| Code | Meaning | Usage |
|------|---------|-------|
| `200 OK` | Success | GET, PUT, PATCH (with response body) |
| `201 Created` | Resource created | POST |
| `202 Accepted` | Async processing started | POST (async operations) |
| `204 No Content` | Success, no body | DELETE, PUT/PATCH (no response body) |

### Client Errors (4xx)

| Code | Meaning | Usage |
|------|---------|-------|
| `400 Bad Request` | Invalid request data | Validation errors |
| `401 Unauthorized` | Missing/invalid auth | No JWT token |
| `403 Forbidden` | Insufficient permissions | Valid token, wrong role |
| `404 Not Found` | Resource doesn't exist | GET/PUT/PATCH/DELETE |
| `409 Conflict` | Resource conflict | Duplicate creation |
| `422 Unprocessable Entity` | Semantic errors | Business logic validation |
| `429 Too Many Requests` | Rate limit exceeded | Rate limiting |

### Server Errors (5xx)

| Code | Meaning | Usage |
|------|---------|-------|
| `500 Internal Server Error` | Server error | Unexpected errors |
| `502 Bad Gateway` | Upstream service error | Service communication |
| `503 Service Unavailable` | Service down | Maintenance, overload |
| `504 Gateway Timeout` | Upstream timeout | Slow service response |

---

## Request Format

### Headers

**Required for all requests:**
```http
Content-Type: application/json
Accept: application/json
```

**For authenticated requests:**
```http
Authorization: Bearer {jwt_token}
```

**For idempotency (critical operations):**
```http
Idempotency-Key: {uuid}
```

**For tracing:**
```http
X-Request-ID: {uuid}
X-Correlation-ID: {uuid}
```

### Request Body (POST/PUT/PATCH)

```json
{
  "field_name": "value",
  "nested_object": {
    "key": "value"
  },
  "array_field": ["item1", "item2"]
}
```

**Field naming:**
- Use `snake_case` for JSON fields
- Match Python naming conventions

---

## Response Format

### Success Response

```json
{
  "id": "uuid-here",
  "field_name": "value",
  "created_at": "2026-01-04T12:34:56.789Z",
  "updated_at": "2026-01-04T12:34:56.789Z"
}
```

### List Response

```json
{
  "items": [
    {
      "id": "uuid-1",
      "name": "Item 1"
    },
    {
      "id": "uuid-2",
      "name": "Item 2"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### Error Response

**Standard error format:**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      },
      {
        "field": "password",
        "message": "Password must be at least 8 characters"
      }
    ],
    "request_id": "uuid-here",
    "timestamp": "2026-01-04T12:34:56.789Z"
  }
}
```

**Error codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `BUSINESS_RULE_VIOLATION` | 422 | Business logic error |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily down |

---

## Pagination

### Query Parameters

```http
GET /api/v1/users?page=1&page_size=20
```

**Parameters:**
- `page` (integer, default: 1) - Page number
- `page_size` (integer, default: 20, max: 100) - Items per page
- `sort` (string) - Sort field
- `order` (asc|desc, default: asc) - Sort order

### Response

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 42,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### Links (Optional, for HATEOAS)

```json
{
  "items": [...],
  "pagination": {...},
  "links": {
    "self": "/api/v1/users?page=2",
    "first": "/api/v1/users?page=1",
    "prev": "/api/v1/users?page=1",
    "next": "/api/v1/users?page=3",
    "last": "/api/v1/users?page=3"
  }
}
```

---

## Filtering & Searching

### Query Parameters

```http
GET /api/v1/restaurants?cuisine=italian&city=moscow&min_rating=4.5
GET /api/v1/orders?status=pending&user_id=123&created_after=2026-01-01
```

### Search

```http
GET /api/v1/restaurants?q=pizza
GET /api/v1/menu-items?search=burger
```

---

## Sorting

```http
GET /api/v1/restaurants?sort=rating&order=desc
GET /api/v1/orders?sort=created_at&order=asc
```

Multiple fields:
```http
GET /api/v1/restaurants?sort=rating,name&order=desc,asc
```

---

## Field Selection (Sparse Fieldsets)

Request only specific fields:

```http
GET /api/v1/users?fields=id,name,email
```

---

## Timestamps

### Format

Use **ISO 8601** format with timezone:

```json
{
  "created_at": "2026-01-04T12:34:56.789Z",
  "updated_at": "2026-01-04T15:30:00.123Z"
}
```

### Timezone

- All timestamps in **UTC**
- Client converts to local timezone

---

## Idempotency

### Idempotency Key

For critical operations (payments, order creation):

```http
POST /api/v1/orders
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

**Behavior:**
- Server stores result with key
- Duplicate requests return same result
- Key expires after 24 hours

---

## Versioning

### URL Versioning

```
/api/v1/users
/api/v2/users
```

**When to version:**
- Breaking changes to request/response format
- Changed business logic
- Removed fields

**Version support:**
- Support at least 2 versions simultaneously
- Deprecation notice 6 months before removal

---

## Rate Limiting

### Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1641312000
```

### Response (when exceeded)

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600
```

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 1 hour.",
    "retry_after": 3600
  }
}
```

---

## CORS

**Allowed origins** (configured in API Gateway):
```
http://localhost:3000
https://app.fooddelivery.com
```

**Allowed methods:**
```
GET, POST, PUT, PATCH, DELETE, OPTIONS
```

**Allowed headers:**
```
Content-Type, Authorization, X-Request-ID, Idempotency-Key
```

---

## WebSocket Conventions

### Connection URL

```
ws://localhost:8005/ws/orders/{order_id}
```

### Message Format

**Client → Server:**
```json
{
  "type": "subscribe",
  "order_id": "uuid-here"
}
```

**Server → Client:**
```json
{
  "type": "location_update",
  "data": {
    "order_id": "uuid-here",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "timestamp": "2026-01-04T12:34:56.789Z"
  }
}
```

---

## Health Check Endpoints

Every service must implement:

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-04T12:34:56.789Z",
  "dependencies": {
    "database": "healthy",
    "kafka": "healthy",
    "redis": "healthy"
  }
}
```

---

## OpenAPI / Swagger

- All services expose `/docs` (Swagger UI)
- All services expose `/openapi.json` (OpenAPI spec)
- Keep OpenAPI spec up-to-date

---

## Examples

### Create Order

**Request:**
```http
POST /api/v1/orders
Content-Type: application/json
Authorization: Bearer eyJhbGc...
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

{
  "restaurant_id": "uuid-here",
  "items": [
    {
      "menu_item_id": "uuid-1",
      "quantity": 2
    },
    {
      "menu_item_id": "uuid-2",
      "quantity": 1
    }
  ],
  "delivery_address": {
    "street": "123 Main St",
    "city": "Moscow",
    "postal_code": "101000"
  }
}
```

**Response:**
```http
HTTP/1.1 201 Created
Location: /api/v1/orders/uuid-order
Content-Type: application/json

{
  "id": "uuid-order",
  "status": "pending",
  "restaurant_id": "uuid-here",
  "total_amount": 1250.00,
  "created_at": "2026-01-04T12:34:56.789Z"
}
```

---

## References

- [REST API Guidelines](https://restfulapi.net/)
- [HTTP Status Codes](https://httpstatuses.com/)
- [JSON:API Specification](https://jsonapi.org/)
