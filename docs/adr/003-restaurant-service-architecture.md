# ADR-003: Restaurant Service Architecture

**Status**: Accepted
**Date**: 2026-01-31
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

Restaurant Service owns restaurant catalog data and menu data. Order creation depends on this service to validate restaurant and menu item inputs before payment reservation and courier assignment.

The service needs to support:
- restaurant creation and updates by owners;
- public restaurant search by indexed filters;
- menu item CRUD and availability changes;
- PostgreSQL persistence with Alembic migrations;
- gateway proxying through `/api/v1/restaurants/*`;
- Kafka publication for catalog changes when event publishing is enabled.

## Decision

Restaurant Service is implemented as a FastAPI service on port `8002` with Clean Architecture boundaries:

```text
src/
├── domain/
├── application/
├── infrastructure/
└── interface/
```

The domain model contains:
- `Restaurant` aggregate with owner id, name, description, address, cuisine, rating, active flag, timestamps;
- `MenuItem` entity with restaurant id, name, description, price, category, image URL, availability, timestamps;
- value objects for address, cuisine, price, category and availability.

Persistence uses PostgreSQL tables:
- `restaurants`, indexed by owner, city, cuisine, rating and creation time;
- `menu_items`, indexed by restaurant, category, availability and creation time.

No database-level foreign key points to User Service. `owner_id` is an external service identifier.

The API exposes:

```http
POST   /api/v1/restaurants
GET    /api/v1/restaurants
GET    /api/v1/restaurants/{restaurant_id}
PUT    /api/v1/restaurants/{restaurant_id}
PATCH  /api/v1/restaurants/{restaurant_id}
DELETE /api/v1/restaurants/{restaurant_id}

GET    /api/v1/restaurants/{restaurant_id}/menu
POST   /api/v1/restaurants/{restaurant_id}/menu-items
GET    /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}
PUT    /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}
PATCH  /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}
PATCH  /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}/availability
DELETE /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}
```

Restaurant Service can publish the current event types, following the shared
`{service}.{aggregate}.{action}` topic convention:
- `restaurant-service.restaurant.created`;
- `restaurant-service.restaurant.updated`;
- `restaurant-service.restaurant.deactivated`;
- `restaurant-service.menu_item.created`;
- `restaurant-service.menu_item.updated`;
- `restaurant-service.menu_item.availability_changed`;
- `restaurant-service.menu_item.deleted`.

## Consequences

### Positive

- Restaurant and menu logic has one owning service.
- Order Service can validate menu data through an explicit HTTP contract.
- The database schema stays simple and queryable with ordinary PostgreSQL indexes.
- Domain and application tests can run without FastAPI or PostgreSQL.

### Negative

- Menu and restaurant reads are served from the write database; there is no dedicated catalog read model.
- Search is filter-based, not full-text ranking.
- Kafka publication is best-effort until an outbox is implemented.

### Risks

- Restaurant catalog search may need a read model or search engine after the filter set grows.
- Menu updates can create cache invalidation work if Redis-backed catalog caching is added later.
- External ownership checks depend on stable identity contracts from User Service and Gateway.

## Alternatives Considered

### Elasticsearch-backed catalog search

**Pros**:
- Better text search and ranking.
- Dedicated read model for catalog browsing.

**Cons**:
- Additional infrastructure and synchronization path.
- Eventual consistency between PostgreSQL and search index.

**Why rejected**: current implementation needs indexed filtering and menu validation more than full-text ranking.

### Menu items embedded as JSONB in restaurants

**Pros**:
- One aggregate can be loaded with one row.
- Simple transactional update of restaurant + menu snapshot.

**Cons**:
- Harder item-level updates, indexing and pagination.
- Less useful for validation queries by item id.

**Why rejected**: menu items need their own identifiers, indexes and lifecycle.

## Implementation Notes

- API routes: `services/restaurant-service/src/interface/api/v1/routes/restaurants.py`
- Domain entities: `services/restaurant-service/src/domain/entities`
- SQLAlchemy models: `services/restaurant-service/src/infrastructure/database/models`
- Repositories: `services/restaurant-service/src/infrastructure/database/repositories`
- Events: `services/restaurant-service/src/infrastructure/events/publisher.py`

## References

- [001-microservices-architecture-baseline.md](001-microservices-architecture-baseline.md)
- [006-clean-architecture-conventions.md](006-clean-architecture-conventions.md)
- [008-postgresql-database-per-service.md](008-postgresql-database-per-service.md)
