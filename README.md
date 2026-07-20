# Agent Control Center

Единое рабочее пространство для управления проектами, задачами и серверными ИИ-агентами с Web-, Desktop- и Android-клиентами.

## Статус

**Specification Draft v0.1.0 — implementation blocked.**

Репозиторий содержит требования и архитектурный baseline. Он не содержит реализации и не даёт разрешения начинать разработку. Перед реализацией обязательны:

1. закрытие блокирующих открытых решений;
2. утверждение спецификации оператором;
3. G1 requirement-completeness PASS;
4. отдельная явная команда на implementation.

## Документы

### Нормативные
- [Каноническое ТЗ](docs/SPECIFICATION.md)
- [Архитектура](docs/ARCHITECTURE.md)
- [Domain Model](docs/DOMAIN_MODEL.md)
- [State Machines](docs/STATE_MACHINES.md)
- [Connector API](docs/CONNECTOR_API.md)
- [Handoff Contract](docs/HANDOFF_CONTRACT.md)
- [Матрица трассируемости](docs/TRACEABILITY.md)
- [Открытые решения](docs/OPEN-QUESTIONS.md)

### Исследования и адаптеры
- [Исследование интеграций](docs/RESEARCH.md)
- [Hermes Agent Adapter](docs/adapters/HERMES.md)

### Паттерны
- [Worker Orchestration](docs/patterns/WORKER_ORCHESTRATION.md)
- [Credential Pools](docs/patterns/CREDENTIAL_POOLS.md)

### Операции
- [Scheduler, Events, Errors, SLO](docs/OPERATIONS.md)
- [Security & Performance](docs/SECURITY_AND_PERFORMANCE.md)
- [Monitoring & Health-check](docs/operations/MONITORING.md)
- [Backup & Recovery](docs/operations/BACKUP.md)

### Проектирование
- [ADR и Sequence Diagrams](docs/ADR_AND_SEQUENCES.md)
- [Roadmap](docs/ROADMAP.md)

### Серия спецификации (внешний аудит)
- [Executive Summary](docs/spec-series/01_Executive_Summary.md)
- [Vision & Scope](docs/spec-series/02_Vision_and_Scope.md)
- [Functional Requirements](docs/spec-series/03_Functional_Requirements.md)
- [Non-Functional Requirements](docs/spec-series/04_Non_Functional_Requirements.md)
- [Domain Model (серия)](docs/spec-series/05_Domain_Model.md)
- [Architecture C4](docs/spec-series/06_Architecture_C4.md)
- [Database Design](docs/spec-series/07_Database_Design.md)
- [API Specification](docs/spec-series/08_API_Specification.md)
- [Event Bus](docs/spec-series/09_Event_Bus.md)
- [Agent Protocol](docs/spec-series/10_Agent_Protocol.md)
- [Connector SDK](docs/spec-series/11_Connector_SDK.md)
- [Security](docs/spec-series/12_Security.md)
- [Observability](docs/spec-series/13_Observability.md)
- [ADR Drafts](docs/spec-series/ADR-DRAFTS.md)
- [Improvement Proposals (рецензия)](docs/spec-series/IMPROVEMENT-PROPOSALS.md)

### Участие
- [Правила участия](CONTRIBUTING.md)

## Ключевой принцип

Agent Control Center не пытается унифицировать внутреннее устройство Hermes, OpenClaw, Claude Code, Codex, ChatGPT/OpenAI и Gemini. Серверный Connector подключает каждый runtime через версионируемый адаптер, публикующий нормализованные capabilities, события, checkpoints и usage-сигналы.

## Предлагаемый MVP

- Web/PWA, desktop wrapper и Android-клиент с общим интерфейсным ядром;
- рабочие пространства, проекты, Kanban-задачи и артефакты;
- реестр серверов, агентов и их capabilities;
- запуск, наблюдение, остановка и ручной handoff работы между агентами;
- общая проектная память, версионируемые skills и wiki;
- квоты/лимиты, approvals, аудит и безопасный outbound-only Connector.

## Лицензия

Лицензия пока не выбрана. Репозиторий приватный; отсутствие файла `LICENSE` означает отсутствие предоставленной публичной лицензии.
