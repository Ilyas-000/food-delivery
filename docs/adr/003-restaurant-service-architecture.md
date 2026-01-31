# ADR-003: Restaurant Service Architecture

**Status**: Proposed
**Date**: 2026-01-31
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

We are building the Restaurant Service as Phase 2 of the Food Delivery platform. This service will manage restaurants, their menus, and menu item availability. It's a critical service that will be consumed by:

- **Order Service**: To validate menu items when creating orders
- **User Service**: Restaurant owners managing their restaurants
- **Analytics Service**: Tracking popular restaurants and dishes
- **Frontend**: Displaying restaurant catalogs and menus to customers

### Forces at Play

**Technical Constraints**:
- Must follow Clean Architecture pattern established in User Service
- Must integrate with existing API Gateway
- PostgreSQL 15 as primary database (already in infrastructure)
- Must support search/filtering for restaurants (by cuisine, location, rating)
- Need to handle menu updates in real-time (availability changes)

**Business Requirements**:
- Restaurant owners can create and manage their restaurants
- Restaurant owners can add/update/delete menu items
- Customers can search restaurants by multiple criteria (cuisine, location, rating, name)
- Menu items can be marked as available/unavailable
- Support for working hours (open/closed status)
- Support for categories (appetizers, mains, desserts, beverages)
- Future: Support for promotions and discounts

**Performance Considerations**:
- Restaurant catalog browsing is read-heavy (90% reads, 10% writes)
- Popular restaurants should be cached
- Search must be fast (<200ms for typical queries)
- Menu updates should be reflected quickly

**Team Skills**:
- Team familiar with Python, FastAPI, SQLAlchemy (from User Service)
- Clean Architecture already established
- Redis available for caching

## Decision

We will implement Restaurant Service with the following architecture:

### 1. Domain Model

**Entities**:
- **Restaurant**: Core aggregate root
  - Properties: `id`, `owner_id`, `name`, `description`, `address`, `cuisine`, `rating`, `is_active`, `created_at`, `updated_at`
  - Business methods: `update_info()`, `activate()`, `deactivate()`, `calculate_rating()`

- **MenuItem**: Entity within Restaurant aggregate
  - Properties: `id`, `restaurant_id`, `name`, `description`, `price`, `category`, `image_url`, `availability`, `created_at`, `updated_at`
  - Business methods: `update_price()`, `mark_available()`, `mark_unavailable()`

**Value Objects**:
- **Cuisine** (Enum): Italian, Chinese, Indian, American, Mexican, Japanese, etc.
- **Price**: Monetary amount with currency (decimal with 2 precision)
- **Address**: Street, city, postal code, coordinates (lat/lon for future delivery radius)
- **Category** (Enum): Appetizer, Main, Dessert, Beverage, Side
- **Availability** (Enum): AVAILABLE, OUT_OF_STOCK, DISCONTINUED

**Domain Events** (for future Kafka integration):
- `RestaurantCreated`
- `RestaurantUpdated`
- `MenuItemAdded`
- `MenuItemUpdated`
- `MenuItemAvailabilityChanged`

### 2. Application Layer

**Use Cases**:
- **CreateRestaurantUseCase**: Restaurant owner creates restaurant
- **UpdateRestaurantUseCase**: Update restaurant info
- **GetRestaurantUseCase**: Get single restaurant by ID
- **SearchRestaurantsUseCase**: Search with filters (cuisine, location, rating, name)
- **AddMenuItemUseCase**: Add item to menu
- **UpdateMenuItemUseCase**: Update menu item
- **UpdateMenuItemAvailabilityUseCase**: Toggle availability (quick operation)
- **DeleteMenuItemUseCase**: Soft delete (mark as discontinued)

**Repository Interfaces**:
- `IRestaurantRepository`: CRUD + search operations
- `IMenuItemRepository`: CRUD + bulk operations

### 3. Infrastructure Layer

**Database Strategy**:
- **Primary Storage**: PostgreSQL with two tables:
  - `restaurants` table with indexes on: `owner_id`, `cuisine`, `is_active`, `rating`
  - `menu_items` table with indexes on: `restaurant_id`, `category`, `availability`
  - Foreign key relationship: `menu_items.restaurant_id -> restaurants.id`

**Search Strategy** (Decision: PostgreSQL Full-Text Search):
- Use PostgreSQL `tsvector` for restaurant name/description search
- Create GIN index on `tsvector` column for fast text search
- Support fuzzy matching with `pg_trgm` extension
- **Why not Elasticsearch**: For MVP, PostgreSQL full-text is sufficient; can migrate later if needed

**Caching Strategy**:
- **Popular Restaurants**: Cache top 100 restaurants in Redis (TTL: 5 minutes)
- **Menu Items**: Cache full menu by `restaurant_id` (TTL: 2 minutes, invalidate on update)
- Cache key pattern: `restaurant:{id}`, `menu:{restaurant_id}`

### 4. API Design

**Endpoints**:
```
# Restaurant Management (Owner only)
POST   /api/v1/restaurants              # Create restaurant
PUT    /api/v1/restaurants/{id}         # Update restaurant
DELETE /api/v1/restaurants/{id}         # Deactivate restaurant

# Restaurant Discovery (Public)
GET    /api/v1/restaurants              # Search/list restaurants
GET    /api/v1/restaurants/{id}         # Get single restaurant
GET    /api/v1/restaurants/{id}/menu    # Get restaurant menu

# Menu Management (Owner only)
POST   /api/v1/restaurants/{id}/menu-items              # Add menu item
PUT    /api/v1/restaurants/{id}/menu-items/{item_id}    # Update menu item
PATCH  /api/v1/restaurants/{id}/menu-items/{item_id}/availability  # Toggle availability
DELETE /api/v1/restaurants/{id}/menu-items/{item_id}    # Delete menu item
```

**Authorization**:
- Restaurant creation: Authenticated users with `RESTAURANT_OWNER` role
- Menu management: Owner of the restaurant only (check `owner_id == current_user.id`)
- Restaurant browsing: Public (no auth required)

### 5. Configuration

**Environment Variables**:
- Prefix: `RESTAURANT_SERVICE_*`
- Database: `RESTAURANT_SERVICE_DB_NAME=restaurant_service_db`
- Port: `8002`
- Redis: `RESTAURANT_SERVICE_REDIS_HOST`, `RESTAURANT_SERVICE_REDIS_DB=2`

## Consequences

### Positive Consequences

- **Consistency**: Follows same Clean Architecture as User Service (easy for team)
- **Performance**: Caching popular restaurants reduces DB load
- **Simplicity**: PostgreSQL full-text search is simpler than Elasticsearch for MVP
- **Scalability**: Can add Elasticsearch later without changing domain logic
- **Separation**: Separate database per service (microservices best practice)
- **Developer Experience**: Familiar patterns, easy to onboard
- **Testing**: Domain/application layers easily testable without infrastructure

### Negative Consequences

- **PostgreSQL Limitations**: Full-text search not as powerful as Elasticsearch
  - Limited ranking algorithms
  - No typo tolerance out-of-box (need `pg_trgm`)
  - Harder to do complex relevance scoring
- **Cache Invalidation**: Need to carefully invalidate Redis cache on updates
- **Duplicate Data**: Restaurant info duplicated in cache (acceptable trade-off)
- **Aggregate Complexity**: Restaurant + MenuItem might grow complex (future refactor risk)

### Risks

**Risk 1: Search Performance Degrades with Scale**
- **Impact**: As restaurants grow to 10k+, PostgreSQL full-text might slow down
- **Mitigation**:
  - Add proper indexes (GIN, trigram)
  - Monitor query performance with `pg_stat_statements`
  - Prepare Elasticsearch migration plan if p95 > 200ms
  - Phase 7 can add Elasticsearch without domain changes

**Risk 2: Cache Stampede on Popular Restaurants**
- **Impact**: If cache expires and 100 requests hit simultaneously, DB overload
- **Mitigation**:
  - Use Redis `SETNX` for distributed locking during cache refresh
  - Implement stale-while-revalidate pattern
  - Set cache TTL with jitter (5min ± 30s)

**Risk 3: Menu Item Count Grows Large (1000+ items per restaurant)**
- **Impact**: Loading full menu becomes slow
- **Mitigation**:
  - Paginate menu items API
  - Add `GET /restaurants/{id}/menu-items?category=mains` filtering
  - Future: Separate read model for menu browsing (CQRS)

## Alternatives Considered

### Alternative 1: Elasticsearch for Search

**Description**: Use Elasticsearch instead of PostgreSQL full-text search

**Pros**:
- Much better search capabilities (typo tolerance, fuzzy matching, relevance scoring)
- Faster for complex queries
- Better analytics (aggregations)
- Industry standard for search

**Cons**:
- Additional infrastructure (complexity, cost, ops burden)
- Data synchronization needed (Elasticsearch = read model, PostgreSQL = source of truth)
- Eventual consistency issues
- Overkill for MVP with <1000 restaurants
- Team needs to learn Elasticsearch

**Why Rejected**: Too complex for MVP. PostgreSQL full-text is sufficient for Phase 2. We can migrate to Elasticsearch in Phase 7 (Analytics) when we have more data and stronger search requirements. The domain layer won't change, only infrastructure.

### Alternative 2: MongoDB for Restaurant Data

**Description**: Use MongoDB (document database) instead of PostgreSQL

**Pros**:
- Natural fit for nested menu items (no joins needed)
- Flexible schema (easy to add fields)
- Built-in text search

**Cons**:
- Breaks microservices pattern (all other services use PostgreSQL)
- Team lacks MongoDB experience
- Additional infrastructure to manage
- Less ACID guarantees (could be issue for inventory)
- Harder to do complex queries and aggregations

**Why Rejected**: Consistency with existing infrastructure is more important. PostgreSQL can handle nested data with JSONB if needed. Team familiarity with PostgreSQL is valuable.

### Alternative 3: Single Table for Restaurant + Menu Items (JSONB)

**Description**: Store menu items as JSONB array in `restaurants.menu_items` column

**Pros**:
- Simpler schema (single table)
- Atomic updates (one transaction)
- Natural aggregate boundary

**Cons**:
- Hard to query individual menu items
- Hard to index menu items separately
- JSONB updates are replace-entire-field (not append)
- Breaks normalization (data duplication if item appears in multiple places)
- Harder to implement pagination for menus

**Why Rejected**: Menu items need their own queries and indexes. Separate table is cleaner and more flexible for future features (e.g., menu item reviews).

### Alternative 4: Event Sourcing for Menu Changes

**Description**: Store menu changes as events instead of current state

**Pros**:
- Full audit trail of all changes
- Can replay history
- Natural for event-driven architecture

**Cons**:
- Much more complex to implement
- Requires event store (additional infrastructure)
- Harder to query current state (need projections)
- Overkill for current requirements
- Team unfamiliar with Event Sourcing

**Why Rejected**: CRUD is sufficient for Restaurant Service. Event Sourcing can be considered for Order Service (Phase 3) where order state transitions are more complex.

## Implementation Notes

### Migration Path

1. **Phase 2.1**: Basic CRUD (no search, no cache) - `feature/restaurant-service-skeleton`
2. **Phase 2.2**: Domain layer (entities, VOs) - `feature/restaurant-service-domain`
3. **Phase 2.3**: Application + Infrastructure (use cases, repos) - `feature/restaurant-service-infrastructure`
4. **Phase 2.4**: API layer - `feature/restaurant-service-api`
5. **Phase 2.5**: Search (PostgreSQL full-text) - can be separate PR
6. **Phase 2.6**: Caching (Redis) - can be separate PR
7. **Phase 2.7**: API Gateway integration - `feature/restaurant-service-gateway`

### Key Components Affected

- **API Gateway**: Add proxy routes for `/api/v1/restaurants/*`
- **Order Service** (Phase 3): Will call Restaurant Service to validate menu items
- **Shared**: Add `RestaurantCreated`, `MenuItemAdded` events

### Database Migration

```sql
-- Create database
CREATE DATABASE restaurant_service_db;
CREATE USER restaurant_service_user WITH PASSWORD '***';
GRANT ALL PRIVILEGES ON DATABASE restaurant_service_db TO restaurant_service_user;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy search

-- Tables created via Alembic migrations
```

### Timeline

- Week 1: Skeleton + Domain + Application (3 days)
- Week 1: Infrastructure + API (2 days)
- Week 2: Search + Caching + Gateway (2 days)
- Week 2: Tests + Documentation (1 day)

**Total**: ~7-8 days for full implementation

### Dependencies

- PostgreSQL 15 (already available)
- Redis 7 (already available)
- API Gateway (already implemented)
- User Service (for owner authentication)

## References

- [DEVELOPMENT-ROADMAP.md](../../DEVELOPMENT-ROADMAP.md) - Phase 2 details
- [PROGRESS.md](../../PROGRESS.md) - Current status
- [API_CONVENTIONS.md](../API_CONVENTIONS.md) - API design standards
- [ENGINEERING_CONVENTIONS.md](../ENGINEERING_CONVENTIONS.md) - Code standards
- User Service implementation - Reference for Clean Architecture patterns
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/15/textsearch.html)
- [Redis Caching Best Practices](https://redis.io/docs/manual/patterns/)

## Examples

### Domain Entity

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

@dataclass
class Restaurant:
    """Restaurant aggregate root."""

    id: UUID
    owner_id: UUID
    name: str
    description: str
    address: Address  # Value Object
    cuisine: Cuisine  # Enum
    rating: Decimal
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        owner_id: UUID,
        name: str,
        description: str,
        address: Address,
        cuisine: Cuisine,
    ) -> "Restaurant":
        """Factory method with validation."""
        if not name or len(name) < 2:
            raise ValueError("Restaurant name must be at least 2 characters")
        if len(name) > 100:
            raise ValueError("Restaurant name too long (max 100 characters)")

        return cls(
            id=uuid4(),
            owner_id=owner_id,
            name=name,
            description=description,
            address=address,
            cuisine=cuisine,
            rating=Decimal("0.0"),  # New restaurants start with 0 rating
        )

    def update_info(
        self,
        name: str | None = None,
        description: str | None = None,
        address: Address | None = None,
    ) -> None:
        """Update restaurant information."""
        if name is not None:
            if len(name) < 2 or len(name) > 100:
                raise ValueError("Invalid name length")
            self.name = name

        if description is not None:
            self.description = description

        if address is not None:
            self.address = address

        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """Activate restaurant (make it visible)."""
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """Deactivate restaurant (hide from customers)."""
        self.is_active = False
        self.updated_at = datetime.now(UTC)
```

### Use Case Example

```python
class CreateRestaurantUseCase:
    """Create a new restaurant."""

    def __init__(
        self,
        restaurant_repository: IRestaurantRepository,
    ) -> None:
        self._restaurant_repository = restaurant_repository

    async def execute(self, dto: CreateRestaurantDTO) -> RestaurantResponseDTO:
        """Execute use case."""
        # 1. Create Address VO
        address = Address(
            street=dto.street,
            city=dto.city,
            postal_code=dto.postal_code,
            latitude=dto.latitude,
            longitude=dto.longitude,
        )

        # 2. Create Restaurant entity
        restaurant = Restaurant.create(
            owner_id=dto.owner_id,
            name=dto.name,
            description=dto.description,
            address=address,
            cuisine=dto.cuisine,
        )

        # 3. Save to repository
        created_restaurant = await self._restaurant_repository.create(restaurant)

        # 4. Return DTO
        return RestaurantResponseDTO.from_entity(created_restaurant)
```

### API Endpoint Example

```python
@router.post(
    "/restaurants",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_restaurant(
    request: CreateRestaurantRequest,
    current_user: Annotated[JWTPayload, Depends(require_role("RESTAURANT_OWNER"))],
    use_case: Annotated[CreateRestaurantUseCase, Depends(get_create_restaurant_use_case)],
) -> RestaurantResponse:
    """Create a new restaurant (restaurant owners only)."""
    dto = CreateRestaurantDTO(
        owner_id=UUID(current_user.user_id),
        name=request.name,
        description=request.description,
        street=request.address.street,
        city=request.address.city,
        postal_code=request.address.postal_code,
        latitude=request.address.latitude,
        longitude=request.address.longitude,
        cuisine=request.cuisine,
    )

    result = await use_case.execute(dto)
    return RestaurantResponse.from_dto(result)
```

---

**Changelog**:
- 2026-01-31: Initial draft
- TBD: Review with team
- TBD: Accepted by Engineering Team
