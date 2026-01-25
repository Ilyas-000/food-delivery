# Technical Debt

## Backlog

- Naming consistency: simplify and clarify naming (DTO/use_case, module names, route names).
- API responses metadata: large inline `responses` blocks in routes should be simplified or moved.

---

## API Gateway Config & Rate Limiting

| # | Issue | Status |
|---|-------|--------|
| 1 | Упростить JWT конфигурацию (AliasChoices, hardcode algorithm) | ✅ Done |
| 2 | Смягчить Rate Limiting для UX | ✅ Done |
| 3 | Endpoint-specific rate limits для Phase 2+ | Pending (Phase 2) |
| 4 | Документация JWT секретов в .env.example | Skipped (не нужно) |

---

## RequestLoggingMiddleware

| # | Issue | Status |
|---|-------|--------|
| 1 | X-Request-ID не передаётся downstream | ✅ Already done |
| 2 | Exception без X-Request-ID | ✅ Done |
| 3 | Дублирование log context | ✅ Done |
| 4 | Реальный client_ip за proxy | ✅ Done |
| 5 | Verbose logging mode | Pending (nice-to-have) |
| 6 | exc_info только в debug | ✅ Done |

---

## CircuitBreakerMiddleware

| # | Issue | Status |
|---|-------|--------|
| 1 | failure_count не сбрасывается | ✅ Done |
| 2 | Жёсткая привязка к URL | Pending (Phase 2) |
| 3 | HALF_OPEN race condition | Pending (Phase 2) |
| 4 | Thread safety для multi-worker | Pending (Production) |
| 5 | Per-service конфигурация | Pending (Phase 2+) |
| 6 | Prometheus metrics | Pending (Phase 10) |

---

## JWT Validator

| # | Issue | Status |
|---|-------|--------|
| 1 | Дублирование кода | ✅ Done |
| 2 | jwt_algorithm избыточен | ✅ Done |
| 3 | Недостаточное логирование | Pending |
| 4 | get_optional_user не различает ошибки | Pending (nice-to-have) |
| 5 | email может быть None | ✅ Done (теперь обязательный) |
| 6 | JTI blacklist | Pending (Phase 2) |
| 7 | Rate limiting на invalid tokens | Pending (Phase 2) |

---

## Rate Limiter

| # | Issue | Status |
|---|-------|--------|
| 1 | client_ip не учитывает proxy | ✅ Done |
| 2 | Дублирование кода | ✅ Done |
| 3 | Retry-After header | Pending (Phase 2) |
| 4 | decode_token_unverified caching | Pending (optimization) |
| 5 | remove_cooldown для admin | Pending (Phase 2) |
| 6 | Error messages дублирование | ✅ Done |
| 7 | Prometheus metrics | Pending (Phase 10) |
