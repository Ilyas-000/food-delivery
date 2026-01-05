# Contributing to Food Delivery

Thank you for your interest in contributing! This document provides guidelines for contributing to the Food Delivery microservices project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Commit Guidelines](#commit-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Architecture Guidelines](#architecture-guidelines)

---

## Getting Started

### Prerequisites

- Python 3.12
- Docker & Docker Compose
- uv (Python package manager)
- Git

### Initial Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/food-delivery.git
   cd food-delivery
   ```

2. **Run the setup script**
   ```bash
   bash scripts/setup-dev.sh
   ```

3. **Verify installation**
   ```bash
   make health
   ```

---

## Development Workflow

### 1. Create a Feature Branch

Always create a new branch from `main`:

```bash
git checkout -b feat/your-feature-name
```

Branch naming conventions:
- `feat/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation changes
- `test/` - Test additions or modifications
- `chore/` - Maintenance tasks

### 2. Make Your Changes

Follow the [Code Standards](#code-standards) section below.

### 3. Run Tests and Linters

Before committing:

```bash
make format      # Format code
make lint        # Check linting
make type-check  # Check types
make test        # Run tests
```

Or run everything at once:

```bash
make pre-commit
```

### 4. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add user registration endpoint"
git commit -m "fix: resolve race condition in order saga"
git commit -m "docs: update API conventions"
```

**Commit message format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Adding or updating tests
- `chore` - Maintenance tasks
- `ci` - CI/CD changes

**Examples:**
```
feat(user-service): add JWT token refresh endpoint

Implements refresh token functionality to improve UX.
Users can now refresh their access tokens without re-login.

Closes #123
```

### 5. Push and Create Pull Request

```bash
git push origin feat/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Code Standards

### Python Code Style

We use **ruff** for linting and formatting:

```bash
make format  # Auto-format code
make lint    # Check linting
```

**Key standards:**
- Line length: 100 characters
- Indentation: 4 spaces
- Quotes: Double quotes
- Type hints: Required for all functions
- Docstrings: Required for public methods

### Type Hints

Always use type hints:

```python
# ✅ Good
def create_order(user_id: int, items: list[OrderItem]) -> Order:
    ...

# ❌ Bad
def create_order(user_id, items):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_total(items: list[OrderItem]) -> Decimal:
    """Calculate total price for order items.

    Args:
        items: List of order items with prices

    Returns:
        Total price as Decimal

    Raises:
        ValueError: If items list is empty
    """
    ...
```

### Clean Architecture Layers

Follow strict layer separation:

```
domain/         # No external dependencies
application/    # Use cases, depends on domain
infrastructure/ # DB, Kafka, Redis - depends on application
interface/      # API, events - depends on application
```

**Rules:**
- Domain layer has ZERO external dependencies
- Infrastructure implements interfaces defined in application
- Use dependency injection

### Error Handling

Use custom domain exceptions:

```python
# domain/exceptions.py
class OrderNotFoundException(Exception):
    pass

# application/use_cases/get_order.py
async def execute(self, order_id: str) -> Order:
    order = await self.repository.get_by_id(order_id)
    if not order:
        raise OrderNotFoundException(f"Order {order_id} not found")
    return order
```

---

## Commit Guidelines

### Conventional Commits

We enforce Conventional Commits via pre-commit hooks.

**Format:**
```
<type>(<scope>): <subject>
```

**Valid types:**
- feat, fix, docs, style, refactor, perf, test, chore, ci

**Examples:**
```bash
feat(order-service): implement saga orchestration
fix(payment-service): handle timeout in payment gateway
docs(api): update OpenAPI specification
test(user-service): add integration tests for auth
refactor(shared): extract kafka producer to base class
```

**Breaking changes:**
```bash
feat(api)!: change order creation response format

BREAKING CHANGE: Order creation now returns order_id instead of full object
```

---

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 80% (enforced by CI)
- **Critical paths**: 90%+ (Saga, payments, auth)

### Test Types

1. **Unit Tests** - Test business logic in isolation
   ```bash
   pytest -m unit
   ```

2. **Integration Tests** - Test with real infrastructure (DB, Kafka)
   ```bash
   pytest -m integration
   ```

3. **E2E Tests** - Test complete flows across services
   ```bash
   pytest -m e2e
   ```

### Writing Tests

```python
# tests/unit/test_create_order.py
import pytest
from src.application.use_cases.create_order import CreateOrderUseCase

@pytest.mark.unit
async def test_create_order_success():
    # Arrange
    use_case = CreateOrderUseCase(mock_repository)

    # Act
    order = await use_case.execute(command)

    # Assert
    assert order.status == OrderStatus.PENDING
```

### Running Tests

```bash
make test           # All tests
make test-unit      # Unit only
make test-cov       # With coverage report
```

---

## Pull Request Process

### Before Submitting

- ✅ All tests pass (`make test`)
- ✅ Code is formatted (`make format`)
- ✅ No linting errors (`make lint`)
- ✅ Type checking passes (`make type-check`)
- ✅ Coverage is ≥80%
- ✅ Documentation updated (if needed)
- ✅ ADR created (for architectural changes)

### PR Title

Use Conventional Commits format:

```
feat(order-service): implement saga compensation logic
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Related Issues
Closes #123
```

### Review Process

1. Automated checks must pass (CI/CD)
2. At least 1 approval required
3. No unresolved conversations
4. Branch must be up-to-date with main

---

## Architecture Guidelines

### Clean Architecture

Each service follows Clean Architecture:

```
src/
├── domain/           # Entities, Value Objects, Domain Events
├── application/      # Use Cases, DTOs, Interfaces
├── infrastructure/   # DB, Kafka, Redis, HTTP clients
└── interface/        # API routes, Kafka consumers
```

### Dependency Rule

Dependencies point inward:
```
Interface → Application → Domain
Infrastructure → Application → Domain
```

### Adding a New Service

Use the template:

```bash
bash scripts/create-service.sh my-new-service
```

This creates the full Clean Architecture structure.

### Event-Driven Communication

All events go through Kafka:

1. Define event in `shared/events/`
2. Publish via Outbox Pattern
3. Subscribe with idempotent handlers

```python
# Publishing
await self.outbox.save(OrderCreatedEvent(order_id=order.id))

# Consuming
async def handle_order_created(event: OrderCreatedEvent):
    # Idempotent processing
    ...
```

### Saga Pattern

For distributed transactions:

1. Order Service orchestrates
2. Each step has compensation
3. Store saga state for recovery

See `docs/architecture/PATTERNS.md` for details.

---

## Questions?

- Read [CLAUDE.md](./CLAUDE.md) for AI agent context
- Check [DEVELOPMENT-ROADMAP.md](./DEVELOPMENT-ROADMAP.md) for current phase
- Review existing [ADRs](./docs/adr/)
- Ask in GitHub Discussions

---

**Happy coding! 🚀**
