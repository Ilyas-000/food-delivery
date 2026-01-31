# Repository Guidelines

## Project Structure & Module Organization
- `shared/`: shared library used by services; code lives in `shared/src/shared` with common utilities, events, and exceptions.
- `docs/`: documentation, including ADRs in `docs/adr/` and API standards in `docs/API_CONVENTIONS.md`.
- `scripts/`: setup and ops helpers (setup, health checks, migrations, seed data).
- `services/`: microservices workspace (created by `scripts/setup-dev.sh` or later phases); each service uses `src/` and `tests/`.
- `tests/`: repo-level integration/e2e tests when present.
- `infrastructure/`: Docker Compose and infra helpers (created by setup or Phase 0 work).

## Build, Test, and Development Commands
- `bash scripts/setup-dev.sh`: bootstrap dev machine, create `.env`, install deps, and initialize directories.
- `make setup-dev`: run `scripts/setup-dev.sh` via Makefile.
- `make dev-install`: install dev dependencies with `uv` and enable pre-commit hooks.
- `make up` / `make down` / `make logs` / `make health`: manage and verify local infrastructure.
- `make migrate` / `make seed`: run DB migrations and load seed data.
- `make test`, `make test-all`, `make test-unit`, `make test-integration`, `make test-e2e`, `make test-cov`: run tests and coverage.
- `make format`, `make lint`, `make type-check`, `make pre-commit`: formatting, linting, typing, and full checks.
- `make dev-user`, `make dev-gateway`: run a specific service locally.

## Coding Style & Naming Conventions
- Python 3.12 with type hints on all functions; Google-style docstrings for public methods.
- Indentation: 4 spaces; line length: 100; quotes: double quotes.
- Format and lint with Ruff (`make format`, `make lint`); type-check with mypy (`make type-check`).
- Follow Clean Architecture boundaries: `domain/` (pure), `application/`, `infrastructure/`, `interface/`.

## Testing Guidelines
- Frameworks: pytest + pytest-asyncio; markers: `unit`, `integration`, `e2e`.
- Default naming: `test_*.py` and `test_*` functions.
- Coverage target is 80% minimum (see `pyproject.toml`); run `make test-cov` to verify.

## Commit & Pull Request Guidelines
- Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`, `test/`, `chore/`.
- Use Conventional Commits (e.g., `feat(user-service): add jwt refresh`).
- Before opening a PR, run `make pre-commit` and ensure coverage stays >= 80%.
- For architectural changes, add an ADR using `docs/adr/template.md`.

## Configuration & Agent Notes
- Copy `.env.example` to `.env` and keep secrets out of Git.
- For contributor context, see `CONTRIBUTING.md`, `AGENT-CONTEXT.md`, and `CLAUDE.md`.
