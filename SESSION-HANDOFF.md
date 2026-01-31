# Session Handoff (Archive)

Date: 2026-01-06
Status: Archived (see PROGRESS.md for current state)

Done:
- Docker compose added (Postgres, Redis, Zookeeper, Kafka, Kafka UI, pgAdmin).
- Kafka dual listeners configured (internal `kafka:9092`, external `localhost:9093`).
- Shared library base utilities and events added.
- Pre-commit passes.

Decisions:
- Python version is 3.12 (project-wide).
- ClickHouse deferred to Phase 7.
- Postgres host port set to 5433 via `.env`.
- Kafka external port is 9093; `KAFKA_ADVERTISED_HOST` in `.env`.
- Kafka UI and pgAdmin enabled.

Commands:
- Start infra: `make up`
- Create topics: `make kafka-topics`
- Health check: `make health`
- Kafka from host: `localhost:9093`
- Kafka from containers: `kafka:9092`
- pgAdmin: `http://localhost:5050` (login from `.env`)
- Kafka UI: `http://localhost:8080`

Notes:
- Zookeeper healthcheck uses `srvr` (ruok is disabled in image).
- Docker compose uses `--env-file .env` via Makefile.
