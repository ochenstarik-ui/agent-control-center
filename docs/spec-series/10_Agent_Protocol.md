# Документ 10. Agent Protocol

## Назначение

Документ определяет протокол взаимодействия AI-агентов в платформе Agent
Control Center, включая регистрацию, выполнение задач, передачу
контекста и восстановление после сбоев.

# 1. Цели протокола

-   Унифицированное взаимодействие агентов.
-   Независимость от поставщика LLM.
-   Поддержка распределенного выполнения.
-   Безопасная передача контекста.
-   Совместимость между версиями.

# 2. Жизненный цикл агента

Состояния:

-   Created
-   Registered
-   Idle
-   Busy
-   WaitingApproval
-   Paused
-   Resuming
-   Completed
-   Failed
-   Offline
-   Decommissioned

Все переходы состояний должны журналироваться.

# 3. Регистрация

При регистрации агент обязан передать:

-   agent_id
-   protocol_version
-   provider
-   model
-   capabilities
-   supported_tools
-   max_context_size

После успешной регистрации агент получает конфигурацию и политики
безопасности.

# 4. Heartbeat

Heartbeat отправляется периодически и содержит:

-   agent_id
-   timestamp
-   current_state
-   active_run_id
-   resource_usage
-   protocol_version

При отсутствии heartbeat в течение заданного интервала агент переводится
в состояние Offline.

# 5. Выполнение задач

Каждая задача содержит:

-   run_id
-   task_id
-   objective
-   context
-   constraints
-   acceptance_criteria
-   timeout
-   priority

# 6. Handoff

При передаче задачи другому агенту передаются:

-   objective
-   current_status
-   completed_steps
-   remaining_steps
-   artifacts
-   memory_links
-   open_questions
-   constraints
-   acceptance_criteria

Передача должна быть атомарной и журналируемой.

# 7. Checkpoint

Агент обязан поддерживать создание контрольных точек:

-   checkpoint_id
-   run_id
-   timestamp
-   execution_state
-   memory_snapshot
-   artifact_references

Checkpoint используется для восстановления после сбоя.

# 8. Восстановление

После восстановления агент:

1.  Загружает последний checkpoint.
2.  Проверяет актуальность контекста.
3.  Возобновляет выполнение.
4.  Публикует событие RunResumed.

# 9. Потоковые события

Агент может публиковать:

-   progress;
-   logs;
-   warnings;
-   partial_results;
-   metrics.

Все события содержат correlation_id и request_id.

# 10. Совместимость

-   Обязательное указание protocol_version.
-   Несовместимые изменения требуют новой версии протокола.
-   Старые версии поддерживаются в течение периода депрекации.

# 11. Требования безопасности

-   Все сообщения подписываются.
-   Используется TLS.
-   Проверяется авторизация агента.
-   Ограничиваются разрешенные инструменты.
-   Все критические действия записываются в Audit.

## Следующий документ

11_Connector_SDK.md
