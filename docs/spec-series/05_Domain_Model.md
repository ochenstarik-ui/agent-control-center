# Документ 05. Domain Model

## Назначение

Документ описывает модель предметной области Agent Control Center,
основные сущности, их связи и жизненный цикл.

## Основные агрегаты

### Organization

Назначение: верхний уровень изоляции данных.

Содержит: - Workspace - Users - Policies - Secrets

### Workspace

Логическая область работы команды.

Содержит: - Projects - Agents - Connectors

### Project

Единица управления разработкой.

Связан с: - Tasks - Runs - Artifacts - Knowledge Base

### Task

Описание работы для агента.

Состояния: - Draft - Ready - Running - WaitingApproval - Completed -
Failed - Cancelled

### Run

Экземпляр выполнения задачи.

Хранит: - входной контекст - журнал событий - результаты - метрики

### Agent

Конфигурация AI-агента.

Свойства: - модель - инструменты - память - разрешения - лимиты

### Connector

Интеграция с внешними системами.

### Artifact

Файл или результат выполнения.

### Memory

Долговременная и кратковременная память.

### Knowledge Base

Коллекция документов с поиском и версионированием.

### Approval

Объект согласования действий.

### Audit Event

Неизменяемая запись о значимом событии.

## Основные связи

Organization → Workspace

Workspace → Projects → Agents → Connectors

Project → Tasks → Runs → Artifacts → Knowledge Base

Run → Events → Metrics → Logs

## Правила модели

-   Все сущности имеют UUID.
-   Используется soft delete, если не указано иначе.
-   Все изменения журналируются.
-   Публичные объекты имеют версионирование.
-   Между Workspace обеспечивается строгая изоляция.

## Следующий документ

06_Architecture_C4.md
