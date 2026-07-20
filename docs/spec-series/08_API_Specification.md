# Документ 08. API Specification

## Назначение

Документ определяет стандарты REST API платформы Agent Control Center,
правила проектирования endpoint'ов, форматы данных и требования к
совместимости.

# 1. Общие принципы

-   REST API с JSON.
-   OpenAPI 3.1.
-   Версионирование через `/api/v1`.
-   UTF-8.
-   UTC для дат и времени.
-   UUID как идентификаторы ресурсов.

# 2. Аутентификация

Поддерживаются: - OAuth2/OIDC; - Bearer Token; - API Keys (для сервисных
интеграций).

Каждый запрос должен содержать корректные учетные данные, если ресурс не
является публичным.

# 3. Структура URL

Примеры:

-   GET /api/v1/projects
-   POST /api/v1/projects
-   GET /api/v1/projects/{project_id}
-   PATCH /api/v1/projects/{project_id}
-   DELETE /api/v1/projects/{project_id}

Аналогичная структура используется для: - workspaces; - tasks; - runs; -
agents; - connectors; - artifacts; - memories; - approvals.

# 4. Правила запросов

-   Использовать HTTP-методы по назначению.
-   Поддерживать пагинацию.
-   Поддерживать фильтрацию.
-   Поддерживать сортировку.
-   Поддерживать идемпотентность для повторяемых операций.

# 5. Формат ответов

Успешный ответ:

``` json
{
  "data": {},
  "meta": {
    "request_id": "uuid"
  }
}
```

Ошибка:

``` json
{
  "error": {
    "code": "ACC-4001",
    "message": "Validation failed"
  },
  "meta": {
    "request_id": "uuid"
  }
}
```

# 6. Коды ошибок

-   400 Bad Request
-   401 Unauthorized
-   403 Forbidden
-   404 Not Found
-   409 Conflict
-   422 Validation Error
-   429 Too Many Requests
-   500 Internal Server Error

Коды ошибок должны соответствовать отдельному каталогу ошибок.

# 7. Версионирование

-   `/api/v1` --- стабильная версия.
-   Несовместимые изменения требуют новой версии API.
-   Устаревшие версии сопровождаются периодом депрекации.

# 8. Идемпотентность

Для операций создания и запуска рекомендуется поддерживать заголовок
`Idempotency-Key`.

# 9. Трассировка

Каждый запрос должен иметь: - request_id; - correlation_id (при наличии
распределенных операций).

# 10. Документация

-   OpenAPI спецификация генерируется автоматически.
-   `/docs` --- Swagger UI.
-   `/redoc` --- ReDoc.
-   `/openapi.json` --- машинное описание API.

## Следующий документ

09_Event_Bus.md
