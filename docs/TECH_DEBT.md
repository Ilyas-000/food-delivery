# Technical Debt

## Backlog

- Naming consistency: simplify and clarify naming (DTO/use_case, module names, route names).
- API responses metadata: large inline `responses` blocks in routes should be simplified or moved.
- Swagger: дублируются разделы auth/authentication в User Service (`/docs`).
- Tests DB: разногласия по стратегии поднятия тестовой БД (auto-create/drop vs ручной жизненный цикл).
- Redis close: mypy не знает про `aclose()` в redis.asyncio, сейчас есть временный type workaround.

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


## 🔧 Technical Debt - Proxy Routes (API Gateway)

### 5. Нет retry логики при network errors
**Проблема:**
- При NetworkError сразу возвращается 502 Bad Gateway
- Временные сбои сети не обрабатываются
- Нет exponential backoff

**Решение:**
Добавить retry с tenacity (или полагаться на Circuit Breaker)

**Note:** Circuit Breaker уже есть, возможно достаточно

**Файлы:**
- `services/api-gateway/src/routes/proxy.py`

**Приоритет:** 🟡 Nice-to-have
**Effort:** 1 час
**Phase:** 2
**Status:** 🟡 Pending (needs analysis with Circuit Breaker)

---

### Summary - Proxy Routes Issues

| # | Issue | Priority | Effort | Phase |
|---|-------|----------|--------|-------|
| 5 | Нет retry логики | 🟡 Nice | 1 hr | 2 |

**Phase 2 focus:** Item #5
**Total recommended:** ~1 час (item 5)

---

## 🔧 Technical Debt - Resilience Strategy (Gateway)

### 1. Ретраи + Circuit Breaker (аналитика и тюнинг)
**Почему важно:**
- Ретраи могут усиливать нагрузку при деградации сервиса
- Circuit Breaker чувствителен к порогам и окнам наблюдения
- Неправильная настройка может ухудшить восстановление

**Что нужно определить:**
- Порог срабатывания (ошибки %) и window
- Совместимость с ретраями (какие ошибки/коды ретраить)
- Backoff стратегия (exponential + jitter)
- Где логически размещать (gateway-only или shared)
- Влияние на SLA и p95/p99

**Вывод:** отдельная аналитическая задача перед внедрением ретраев

**Приоритет:** 🟠 Medium
**Effort:** 2-4 часа
**Phase:** 2
**Status:** 🟡 Pending
