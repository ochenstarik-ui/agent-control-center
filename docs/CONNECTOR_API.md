# Connector API v1

**Версия:** 0.1.0-draft | **Статус:** Draft

## Transport

- **Протокол:** WSS (WebSocket Secure) + HTTPS fallback
- **Аутентификация:** mTLS (клиентский сертификат) + JWT
- **Формат:** JSON (все payloads)
- **Сжатие:** per-message deflate (опционально)
- **Keepalive:** ping/pong каждые 30 секунд

## Endpoints

### 1. register
Регистрация коннектора при первом подключении.

```json
// → Request
{
  "type": "register",
  "connector_id": "uuid",
  "version": "1.0.0",
  "host": "server01.example.com",
  "adapters": ["hermes", "openclaw"]
}

// ← Response
{
  "type": "register_ack",
  "connector_id": "uuid",
  "server_time": "2026-07-20T12:00:00Z",
  "config": { ... }
}
```

### 2. heartbeat
Периодический health-check.

```json
// → Request (каждые 30s)
{
  "type": "heartbeat",
  "connector_id": "uuid",
  "timestamp": "2026-07-20T12:00:30Z",
  "metrics": {
    "cpu_pct": 45.2,
    "memory_mb": 512,
    "active_runs": 2,
    "queued_runs": 1
  }
}

// ← Response
{ "type": "heartbeat_ack" }
```

### 3. capabilities
Объявление возможностей коннектора и его агентов.

```json
// → Request
{
  "type": "capabilities",
  "connector_id": "uuid",
  "agents": [{
    "agent_id": "uuid",
    "runtime": "hermes",
    "model": "opencode-go/kimi-k2.7-code",
    "tools": ["terminal", "browser", "file", "delegation"],
    "max_turns": 60,
    "supports": ["streaming", "cancellation", "handoff"]
  }]
}
```

### 4. create_run
Запуск задачи на агенте.

```json
// → Request
{
  "type": "create_run",
  "run_id": "uuid",
  "agent_id": "uuid",
  "goal": "Research GRPO papers",
  "context_bundle": {
    "objective": "...",
    "acceptance_criteria": ["..."],
    "memory_keys": ["key1", "key2"],
    "artifacts": ["artifact-id-1"]
  },
  "constraints": {
    "max_tokens": 100000,
    "timeout_seconds": 600,
    "tools": ["terminal", "browser"]
  }
}

// ← Response
{
  "type": "run_accepted",
  "run_id": "uuid",
  "status": "queued"
}
```

### 5. stream_events
Поток событий от агента (server → client push).

```json
{
  "type": "run_event",
  "run_id": "uuid",
  "event": "tool_call",
  "timestamp": "2026-07-20T12:01:00Z",
  "payload": {
    "tool": "terminal",
    "command": "ls -la",
    "output": "total 48\n..."
  }
}
```

Типы событий: `thinking`, `tool_call`, `tool_result`, `progress`, `warning`, `error`, `completion`.

### 6. cancel_run
Отмена запущенной задачи.

```json
// → Request
{ "type": "cancel_run", "run_id": "uuid" }
// ← Response
{ "type": "run_cancelled", "run_id": "uuid" }
```

### 7. handoff
Передача контекста между агентами.

```json
// → Request
{
  "type": "handoff",
  "from_run_id": "uuid",
  "to_agent_id": "uuid",
  "bundle": {
    "objective": "...",
    "progress": "...",
    "decisions": ["..."],
    "artifacts": ["id1"],
    "open_questions": ["..."]
  }
}
```

### 8. upload_artifact / download_artifact
Загрузка/выгрузка артефактов через Object Storage.

```json
// → upload_artifact
{
  "type": "upload_artifact",
  "run_id": "uuid",
  "name": "results.csv",
  "content_type": "text/csv",
  "size_bytes": 1024
}
// ← Response: { "upload_url": "https://...", "artifact_id": "uuid" }

// → download_artifact
{ "type": "download_artifact", "artifact_id": "uuid" }
// ← Response: { "download_url": "https://..." }
```

### 9. approve
Запрос подтверждения опасного действия.

```json
// → Request (connector → server)
{
  "type": "approval_request",
  "run_id": "uuid",
  "action": "rm -rf /tmp/build",
  "risk_level": "high"
}

// ← Response (server → connector, after human approval)
{
  "type": "approval_granted",
  "approval_id": "uuid",
  "approved_by": "user@example.com"
}
```

## Коды ошибок

| Код | Описание |
|---|---|
| 4001 | Invalid request format |
| 4002 | Unknown message type |
| 4003 | Agent not found |
| 4004 | Run not found |
| 4005 | Agent busy (max concurrent runs) |
| 4006 | Quota exceeded |
| 4007 | Unauthorized action |
| 4008 | Approval denied |
| 5001 | Connector internal error |
| 5002 | Adapter error |

## Retry Policy

| Ошибка | Стратегия |
|---|---|
| Network timeout | Exponential backoff: 1s, 2s, 4s, 8s, 16s, затем каждые 30s |
| 5001/5002 | Мгновенный retry × 3, затем fail |
| 4005 | Отложить run в очередь, retry через 60s |
| 4006 | Остановить run, уведомить operator |

## Таймауты

| Операция | Таймаут |
|---|---|
| register | 10s |
| heartbeat response | 5s |
| create_run accept | 30s |
| stream_event доставка | 60s (затем reconnect) |
| cancel_run подтверждение | 15s |
| upload_artifact URL | 300s |
