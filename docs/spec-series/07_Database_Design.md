# Документ 07. Database Design

## Назначение

Документ описывает архитектуру базы данных Agent Control Center, модель
хранения данных, правила проектирования схем, миграции и требования к
производительности.

# 1. Общие требования

-   Основная СУБД: PostgreSQL 16+
-   UUID в качестве первичных ключей.
-   UTC для всех временных меток.
-   Миграции через Alembic.
-   Soft Delete по умолчанию.
-   Поля created_at и updated_at обязательны.

# 2. Основные таблицы

## organizations

Хранение организаций.

Основные поля: - id (UUID) - name - slug - status - created_at -
updated_at

## workspaces

Связаны с organization.

Поля: - id - organization_id - name - description

## users

Поля: - id - email - display_name - status

## roles

Поля: - id - name - description

## projects

Поля: - id - workspace_id - name - status - version

## tasks

Поля: - id - project_id - title - state - priority

## runs

Поля: - id - task_id - agent_id - state - started_at - finished_at

## agents

Поля: - id - workspace_id - provider - model - configuration_json

## connectors

Поля: - id - type - status - capabilities_json

## artifacts

Поля: - id - run_id - storage_uri - checksum - size_bytes

## memories

Поля: - id - workspace_id - memory_type - embedding_id - metadata_json

## knowledge_documents

Поля: - id - workspace_id - title - version - source

## approvals

Поля: - id - run_id - requested_by - approved_by - state

## audit_events

Поля: - id - actor_id - entity_type - entity_id - action - created_at

# 3. Индексы

Рекомендуемые индексы:

-   organization_id
-   workspace_id
-   project_id
-   task_id
-   run_id
-   state
-   created_at
-   updated_at

GIN: - metadata_json - capabilities_json

# 4. Ограничения

-   Внешние ключи обязательны.
-   CHECK для состояний.
-   UNIQUE для slug и email.
-   ON DELETE RESTRICT для критичных сущностей.

# 5. Миграции

Правила:

-   одна миграция --- одно изменение;
-   обратимые миграции;
-   автоматическая проверка в CI;
-   тестирование миграций на пустой и заполненной БД.

# 6. Производительность

Целевые показатели:

-   поиск по PK \< 10 мс;
-   типовые SELECT \< 100 мс;
-   поддержка партиционирования для audit_events и artifacts.

# 7. Архивирование

-   Архив завершённых Run.
-   Политики хранения Audit.
-   Очистка временных артефактов по TTL.

## Следующий документ

08_API_Specification.md
