# Architecture Decision Records

**Версия:** 0.1.0-draft | **Статус:** Draft

## Шаблон ADR

```markdown
# ADR-NNN: Краткое название

**Статус:** proposed | accepted | deprecated | superseded
**Дата:** YYYY-MM-DD
**Владельцы:** @username
**Связано:** OQ-XXX, FR-XXX, NFR-XXX

## Контекст

Описание проблемы, требующей архитектурного решения. Какие силы действуют?
Какие ограничения?

## Варианты и анализ

### Вариант A: Название
- **Плюсы:** ...
- **Минусы:** ...
- **Риски:** ...

### Вариант B: Название
- **Плюсы:** ...
- **Минусы:** ...

## Решение

Выбран **Вариант X** потому что ...

## Последствия

### Положительные
- ...

### Отрицательные
- ...

### Безопасность и приватность
- ...

### Операционные
- ...

## Миграция и откат

Как перейти от текущего состояния к новому? Как откатиться?

## Валидация

Как проверить, что решение работает?
```

## Каталог ADR

| Номер | Название | Статус | Дата |
|---|---|---|---|
| ADR-001 | Client stack: React + Tauri + Capacitor | proposed | — |
| ADR-002 | Auth: OIDC + local bootstrap | proposed | — |
| ADR-003 | Persistence: PostgreSQL + Object Storage | proposed | — |
| ADR-004 | WSS transport for Connector | proposed | — |
| ADR-005 | Adapter pattern: versioned, capability-based | proposed | — |
| ADR-006 | Handoff format: JSON Schema v1 | proposed | — |
| ADR-007 | Event Bus: PostgreSQL NOTIFY/LISTEN vs Redis | proposed | — |
| ADR-008 | Memory embeddings: pgvector vs external | proposed | — |
| ADR-009 | Connector sandbox: container vs systemd | proposed | — |
| ADR-010 | API versioning: URL-based (/v1, /v2) | proposed | — |

## Sequence Diagrams (текстовые)

### Запуск проекта (happy path)

```
User → API: POST /projects (name, workspace)
API → DB: INSERT project
API → User: 201 { project_id }

User → API: POST /tasks (project_id, title)
API → Scheduler: enqueue(task)
Scheduler → Connector: create_run(agent, goal)
Connector → Agent: run(goal)
Agent → Connector: stream_events(...)
Connector → API: stream_events(...)
API → User: WSS push events
Agent → Connector: run_completed
Connector → API: run_completed
API → User: notification
```

### Handoff

```
Agent_A → Connector_A: handoff(agent_B, bundle)
Connector_A → API: handoff_request
API → Scheduler: enqueue(agent_B, bundle)
Scheduler → Connector_B: create_run(agent_B, bundle)
Agent_B → Connector_B: run_accepted
Connector_B → API: handoff_ack
API → Connector_A: handoff_ack
```

### Approval

```
Agent → Connector: approval_request(action="rm -rf /build", risk=high)
Connector → API: approval_request
API → EventBus: approval.requested
EventBus → User: push notification
User → API: POST /approvals/{id}/approve
API → Connector: approval_granted
Connector → Agent: continue
Agent → Connector: action_executed
```

### Восстановление после reconnect

```
Connector → API: register (reconnect)
API → Connector: register_ack + pending_commands[]
Connector → Agent: resume(run_id)
Agent → Connector: stream_events (с последнего checkpoint)
Connector → API: stream_events
API → User: events replayed
```
