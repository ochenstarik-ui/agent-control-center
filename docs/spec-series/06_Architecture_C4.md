# Документ 06. Architecture (C4)

## Назначение

Документ описывает архитектуру системы по модели C4.

# C1. System Context

Внешние участники: - Пользователь - AI Provider - Git - CI/CD -
PostgreSQL - Object Storage - Message Broker

# C2. Containers

-   Web UI
-   REST API
-   Run Orchestrator
-   Scheduler
-   Agent Runtime
-   Connector Gateway
-   Memory Service
-   Knowledge Service
-   Event Bus
-   Audit Service

# C3. Components

## API

-   Auth
-   Projects
-   Runs
-   Agents
-   Connectors
-   Admin

## Orchestrator

-   Planner
-   Executor
-   Retry Manager
-   Approval Manager

## Memory

-   Vector Index
-   Metadata Store
-   Retrieval

# C4. Code

Рекомендуемая структура:

    app/
     core/
     api/
     services/
     repositories/
     models/
     workers/
     events/
     integrations/
     tests/

# Принципы

-   API First
-   Event Driven
-   Stateless сервисы
-   Горизонтальное масштабирование
-   Idempotency
-   Dependency Injection

# Масштабирование

-   API масштабируется независимо.
-   Workers масштабируются по очередям.
-   Memory Service выделяется в отдельный сервис.
-   Event Bus поддерживает асинхронную обработку.

## Следующий документ

07_Database_Design.md
