# Agents Rules - Code Style and Conventions

This file contains mandatory rules for AI agents working on this codebase.

## Critical Rules

### 1. __init__.py Files
- **NEVER add imports to __init__.py files**
- Only include a simple docstring
- Example:
  ```python
  """Domain entities - business objects with identity."""
  ```
- Users import directly from modules: `from src.domain.entities.restaurant import Restaurant`

### 2. Docstrings and Comments
- **Keep docstrings minimal**
- Only add docstrings for:
  - Module level (one-liner)
  - Class level (one-liner)
  - Complex/non-obvious methods
- **NEVER add docstrings for:**
  - Simple getters/setters
  - Obvious CRUD operations
  - Self-explanatory methods
- **Comments only for non-obvious logic**
- Example of GOOD docstring:
  ```python
  class RestaurantModel(Base):
      """SQLAlchemy model for restaurants table."""
  ```
- Example of BAD docstring (too verbose):
  ```python
  class RestaurantModel(Base):
      """
      SQLAlchemy model for restaurants table.

      Uses SQLAlchemy 2.0 style with Mapped and mapped_column.

      Table structure:
      - id: UUID primary key
      - name: Restaurant name
      ...
      """
  ```

### 3. Imports
- **ALL imports at the top of the file**
- NEVER put imports inside methods/functions
- Exception: Only when absolutely necessary for circular dependency resolution

### 4. Follow Existing Patterns
- **Study User Service before implementing similar features**
- Match the style, structure, and patterns exactly
- Don't reinvent - copy the pattern

## Architecture Rules

### Clean Architecture Layers
```
domain/          # Pure Python, no framework dependencies
  entities/      # Business objects with identity
  value_objects/ # Immutable objects compared by value
  exceptions/    # Domain-specific exceptions

application/     # Use cases, DTOs, interfaces
  use_cases/     # Business workflows (orchestration only)
  dto/           # Pydantic models for data transfer
  interfaces/    # Repository interfaces (Dependency Inversion)

infrastructure/  # External concerns (DB, cache, etc.)
  database/
    models/      # SQLAlchemy ORM models
    repositories/# Repository implementations

interface/       # API layer
  api/v1/
    routes/      # FastAPI endpoints
    schemas/     # Request/Response Pydantic models
```

### Domain Layer Rules
- **NO external dependencies** (no SQLAlchemy, no FastAPI, no Redis)
- Only Python standard library + dataclasses
- Business logic ONLY in entities, not in use cases
- Use factory methods (`.create()`) for entity creation
- Validation in `__post_init__` for value objects

### Application Layer Rules
- Use cases orchestrate workflow, NO business logic
- DTOs use Pydantic BaseModel
- Interfaces use ABC (Abstract Base Class)
- Use cases depend on interfaces, not implementations

### Infrastructure Layer Rules
- Models use SQLAlchemy 2.0 style (`Mapped`, `mapped_column`)
- Repository implements interface from application layer
- Mapping methods: `_entity_to_model()`, `_model_to_entity()`
- Use structlog for logging
- Handle database errors (IntegrityError, etc.)

### API Layer Rules
- FastAPI with lifespan events
- Pydantic schemas for request/response
- Dependency injection for repositories
- Proper HTTP status codes
- Error handling middleware

## Technical Standards

### Database
- PostgreSQL with asyncpg driver
- SQLAlchemy 2.0 async style
- UUID primary keys (not auto-increment)
- Timestamps always in UTC
- Indexes on foreign keys and frequently queried fields
- Use ENUMs for type safety
- No hard foreign keys between microservices

### Validation
- Pydantic for DTOs and API schemas
- Domain validation in entities/value objects
- Use `Field()` with constraints (min_length, max_length, ge, le)

### Error Handling
- Domain exceptions inherit from base DomainError
- Specific exceptions: NotFoundError, AlreadyExistsError, InvalidDataError
- Repository catches IntegrityError and raises domain exception

### Logging
- Use structlog
- Log at entry/exit of repository operations
- Include relevant context (IDs, operation type)
- Levels: debug (queries), info (operations), warning (not found), exception (errors)

### Testing
- Unit tests for domain layer (pure Python)
- Integration tests for repositories (with real DB)
- E2E tests for API endpoints
- Use pytest with async support
- Mock external dependencies

## Code Quality

### Linting
- Ruff for linting and formatting
- Follow pyproject.toml configuration
- Fix all errors before committing
- Exceptions only when truly necessary (add to pyproject.toml)

### Git
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Logical branch names: `feature/restaurant-service-domain`
- Merge feature branches into main feature branch before merging to main
- Always include: `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`

### Pre-commit Hooks
- Always run before committing
- Fix issues, don't skip hooks
- If hook fails on commit, fix and recommit (don't amend unless user asks)

## Don't Do This

- ❌ Don't add `__all__` to __init__.py files
- ❌ Don't write verbose docstrings explaining obvious code
- ❌ Don't add comments for every line
- ❌ Don't put imports inside methods
- ❌ Don't create files unless necessary
- ❌ Don't add features not requested
- ❌ Don't use emojis (unless user explicitly requests)
- ❌ Don't create markdown/documentation files proactively
- ❌ Don't over-engineer (keep it simple)
- ❌ Don't add error handling for impossible scenarios

## Do This

- ✅ Read User Service code before implementing similar features
- ✅ Keep docstrings short and minimal
- ✅ Comment only non-obvious logic
- ✅ Put all imports at the top
- ✅ Follow Clean Architecture principles
- ✅ Use Repository Pattern for data access
- ✅ Validate at domain layer
- ✅ Use factory methods for entity creation
- ✅ Handle errors properly with domain exceptions
- ✅ Write tests
- ✅ Run linter before committing
- ✅ Ask user for clarification when uncertain

## Remember

This is a **learning codebase** for interviews and education. The patterns here are intentionally explicit and well-structured. Follow them exactly.
