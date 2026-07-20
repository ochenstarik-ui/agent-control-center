# Operations: Scheduler, Events, Errors, SLO

**Версия:** 0.1.0-draft | **Статус:** Draft

## 1. Scheduler

Приоритетная очередь запусков с поддержкой fair scheduling.

### Очереди

| Очередь | Приоритет | Описание |
|---|---|---|
| Priority Queue | 0 (высший) | Критические задачи, ручной запуск |
| Fair Queue | 1 | Обычные задачи, round-robin по workspace |
| Retry Queue | 2 | Задачи после transient failure |
| Delayed Queue | 3 | Отложенные задачи (cron, schedule) |
| Approval Queue | — | Задачи, ожидающие approval (блокируют слот агента) |

### Параметры планировщика

| Параметр | Значение |
|---|---|
| Макс. concurrent runs на connector | 5 |
| Макс. concurrent runs на agent | 1 |
| Preemption | Выключена в MVP |
| Fair share | Минимум 1 слот на workspace |
| Retry backoff | 1min, 5min, 15min, 1h, затем fail |
| Max queued per workspace | 100 |

## 2. Event Bus

Durable event bus с гарантией at-least-once доставки.

### События

| Событие | Payload | Частота |
|---|---|---|
| `run.created` | run_id, task_id, agent_id, goal | ~1/min |
| `run.started` | run_id, connector_id, timestamp | ~1/min |
| `run.completed` | run_id, duration, tokens, cost | ~1/min |
| `run.failed` | run_id, error_code, error_message | ~0.1/min |
| `run.cancelled` | run_id, cancelled_by | ~0.05/min |
| `approval.requested` | approval_id, run_id, action, risk | ~2/day |
| `approval.granted` | approval_id, approved_by | ~2/day |
| `approval.denied` | approval_id, denied_by, reason | ~0.5/day |
| `connector.online` | connector_id, version, agents | ~0.1/day |
| `connector.offline` | connector_id, last_heartbeat | ~0.1/day |
| `connector.degraded` | connector_id, missed_heartbeats | ~0.2/day |
| `artifact.created` | artifact_id, run_id, name, size | ~5/min |
| `memory.updated` | memory_id, key, scope, version | ~1/min |
| `skill.registered` | skill_id, name, version | ~0.1/day |

### Гарантии доставки

| Свойство | Значение |
|---|---|
| Доставка | At-least-once |
| Порядок | Per-run (внутри одного run — строгий порядок) |
| Дедупликация | По event_id (idempotency key) |
| Хранение | 30 дней |
| Версионирование | Все схемы эволюционируют additive-only |

## 3. Error Catalog

Единый каталог ошибок с кодами по подсистемам.

| Код | Подсистема | Описание | HTTP |
|---|---|---|---|
| AUTH-001 | Auth | Invalid credentials | 401 |
| AUTH-002 | Auth | Token expired | 401 |
| AUTH-003 | Auth | Insufficient permissions | 403 |
| CONN-001 | Connector | Registration failed | 400 |
| CONN-002 | Connector | Heartbeat timeout | 408 |
| CONN-003 | Connector | Version incompatible | 409 |
| RUN-001 | Run | Agent busy | 409 |
| RUN-002 | Run | Quota exceeded | 429 |
| RUN-003 | Run | Invalid goal format | 400 |
| RUN-004 | Run | Run not found | 404 |
| APPROVAL-001 | Approval | Self-approval denied | 403 |
| APPROVAL-002 | Approval | Approval expired | 410 |
| ARTIFACT-001 | Artifact | Upload failed | 500 |
| ARTIFACT-002 | Artifact | Size limit exceeded | 413 |
| MEM-001 | Memory | Key conflict | 409 |
| SKILL-001 | Skill | Signature invalid | 403 |
| WIKI-001 | Wiki | Page locked | 423 |

## 4. SLO / SLA

Целевые показатели качества обслуживания.

### SLO (Service Level Objectives)

| Метрика | Цель | Окно |
|---|---|---|
| API availability | 99.5% | monthly |
| p95 latency (REST read) | < 200ms | rolling 1h |
| p95 latency (REST write) | < 500ms | rolling 1h |
| Event delivery (p95) | < 2s | rolling 1h |
| Run dispatch (p99) | < 10s | rolling 1h |
| Search latency (p95) | < 500ms | rolling 1h |
| Artifact upload (p95) | < 30s per MB | rolling 1h |

### SLA (Service Level Agreements) — целевые, не контрактные в MVP

| Метрика | Цель |
|---|---|
| Time to detect connector offline | < 90s |
| Time to recover connector | < 5min (ручной) |
| Max data loss (events) | < 5min окно |
| RPO (артефакты) | < 1h |
| RTO (полное восстановление) | < 4h |

## 5. API Versioning

| Версия | Статус | Дата |
|---|---|---|
| /api/v1 | Draft | Q3 2026 |
| /api/v2 | Planned | Q1 2027 (breaking changes) |

**Правила:**
- MAJOR version в URL (/api/v1, /api/v2)
- MINOR changes — additive (новые поля, эндпоинты)
- Deprecation: минимум 3 месяца уведомления через Sunset header
- Старые версии: 6 месяцев поддержки после выхода новой MAJOR
