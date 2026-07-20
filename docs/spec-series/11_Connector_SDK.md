# Документ 11. Connector SDK

## Назначение

Спецификация SDK для интеграции внешних систем с Agent Control Center.

# 1. Требования

Коннектор обязан:

-   поддерживать Protocol v1;
-   проходить регистрацию;
-   отправлять heartbeat;
-   публиковать события;
-   поддерживать безопасную аутентификацию.

# 2. Жизненный цикл

Created → Registered → Online → Busy → Offline → Retired

# 3. Обязательные операции

-   register()
-   heartbeat()
-   capabilities()
-   execute()
-   cancel()
-   upload_artifact()
-   download_artifact()
-   publish_event()

# 4. Capability Discovery

Коннектор публикует:

-   поддерживаемые инструменты;
-   ограничения;
-   максимальный размер данных;
-   поддерживаемые версии протокола.

# 5. Безопасность

-   TLS 1.3+
-   OAuth2/API Key
-   Подпись сообщений
-   Проверка разрешений
-   Ограничение частоты запросов

# 6. Обработка ошибок

Категории:

-   Authentication
-   Authorization
-   Validation
-   Network
-   Timeout
-   Internal

Повторная отправка допускается только для идемпотентных операций.

# 7. Совместимость

SDK обязан поддерживать семантическое версионирование и публиковать
protocol_version.

# 8. Рекомендации

-   Структурированное логирование
-   Метрики Prometheus
-   Health endpoint
-   Graceful shutdown
-   Автоматическое восстановление соединения

## Следующий документ

12_Security.md
