# Документ 09. Event Bus

## Назначение

Документ описывает событийную архитектуру платформы Agent Control
Center, правила публикации и обработки событий.

# 1. Принципы

-   Event Driven Architecture.
-   Асинхронная обработка.
-   Слабая связанность сервисов.
-   Идемпотентные обработчики.
-   Повторная доставка допустима.

# 2. Категории событий

## Lifecycle

-   RunCreated
-   RunScheduled
-   RunStarted
-   RunPaused
-   RunResumed
-   RunCompleted
-   RunFailed
-   RunCancelled

## Project

-   ProjectCreated
-   ProjectUpdated
-   ProjectArchived

## Agent

-   AgentCreated
-   AgentUpdated
-   AgentDeleted

## Connector

-   ConnectorRegistered
-   ConnectorOnline
-   ConnectorOffline
-   ConnectorHeartbeat

## Memory

-   MemoryCreated
-   MemoryUpdated
-   MemoryDeleted

## Artifact

-   ArtifactUploaded
-   ArtifactDeleted

## Security

-   UserLoggedIn
-   PermissionChanged
-   ApprovalRequested
-   ApprovalGranted
-   ApprovalRejected

# 3. Формат сообщения

Каждое событие содержит: - event_id - event_type - event_version -
occurred_at - producer - correlation_id - payload

# 4. Гарантии

-   At-least-once delivery.
-   Идемпотентность обработчиков обязательна.
-   Сохранение порядка в пределах одного aggregate.

# 5. Повторная обработка

Использовать: - retry policy; - dead-letter queue; - экспоненциальную
задержку.

# 6. Наблюдаемость

Каждое событие журналируется и имеет трассировку.

## Следующий документ

10_Agent_Protocol.md
