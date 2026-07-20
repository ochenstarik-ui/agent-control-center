# Документ 13. Observability

## Назначение

Документ определяет требования к наблюдаемости (Observability) платформы
Agent Control Center: логирование, метрики, распределённую трассировку,
мониторинг и эксплуатационные показатели.

# 1. Цели

-   Быстрое обнаружение проблем.
-   Сокращение MTTR.
-   Полная трассировка выполнения Run.
-   Контроль производительности компонентов.
-   Возможность анализа инцидентов.

# 2. Логирование

Все сервисы должны использовать структурированные JSON-логи.

Минимальные поля: - timestamp - level - service - request_id -
correlation_id - run_id - user_id - message

Уровни: - DEBUG - INFO - WARNING - ERROR - CRITICAL

# 3. Метрики

Экспорт через Prometheus.

Основные метрики: - HTTP Requests/sec - Error Rate - P95/P99 Latency -
Active Runs - Queue Length - Memory Usage - CPU Usage - Connector
Availability

# 4. Distributed Tracing

Поддержка OpenTelemetry.

Каждый запрос должен формировать Trace ID и Span ID.

Трассируются: - API - Event Bus - Scheduler - Agent Runtime - Connector
SDK - Database

# 5. Health Checks

Обязательные endpoints:

-   /health/live
-   /health/ready
-   /metrics

Проверяются: - PostgreSQL - Event Bus - Object Storage - AI Provider -
Memory Service

# 6. Alerting

Рекомендуемые правила:

-   высокая доля ошибок;
-   рост задержек;
-   отсутствие heartbeat;
-   переполнение очередей;
-   исчерпание дискового пространства.

# 7. SLI / SLO

Пример целевых значений:

-   API Availability ≥ 99.9%
-   P95 API Latency \< 500 ms
-   Error Rate \< 1%
-   Recovery Time \< 15 min

# 8. Эксплуатация

Все сервисы должны поддерживать: - graceful shutdown; - readiness
probe; - liveness probe; - безопасный перезапуск.

## Следующий документ

14_Testing_Strategy.md
