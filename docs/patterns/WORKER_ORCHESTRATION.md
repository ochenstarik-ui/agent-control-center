# Worker Orchestration Patterns

**Версия:** 0.1.0-draft
**Дата:** 2026-07-20
**Статус:** Draft
**Зависит от:** `SPECIFICATION.md`, `ARCHITECTURE.md`, `docs/adapters/HERMES.md`

> Этот документ описывает паттерны оркестрации через worker-профили Hermes Agent. Реализация запрещена до G0/G1 и утверждения оператором.

## 1. Обзор

Worker-профили Hermes Agent (`worker-code`, `worker-fast`, `worker-research`, `worker-review`) обеспечивают изолированное выполнение специализированных задач. Оркестратор (`default` профиль) маршрутизирует подзадачи, управляет fallback'ами и агрегирует результаты.

Архитектура оркестрации:
```
Пользователь → default (оркестратор)
                    ├──→ worker-code    (opencode-go / kimi-k2.7-code)
                    ├──→ worker-fast    (fireworks / grok-4.5)
                    ├──→ worker-research (gemini / gemini-3-flash-preview)
                    └──→ worker-review   (nvidia / deepseek-v4-pro)
```

## 2. Маршрутизация задач

### 2.1 Матрица маршрутизации

| Тип задачи | Первичный профиль | Вторичный (fallback) | Критерий выбора |
|---|---|---|---|
| **Генерация кода** | `worker-code` | `worker-fast` | Задача содержит "напиши код", "реализуй", "создай файл" |
| **Рефакторинг** | `worker-code` | `worker-review` | Задача требует изменения существующего кода с сохранением поведения |
| **Отладка** | `worker-code` | `worker-research` | Задача содержит трассировку, ошибку, stack trace |
| **Быстрый ответ** | `worker-fast` | `worker-code` | Задача простая, не требует сложного рассуждения |
| **Исследование** | `worker-research` | `worker-code` | Задача требует анализа документации, поиска, чтения |
| **Code Review** | `worker-review` | `worker-code` | Задача проверки качества/безопасности кода |
| **Аудит безопасности** | `worker-review` | `worker-research` | Задача анализа уязвимостей, проверки политик |
| **Планирование** | `default` (in-process) | `worker-research` | Задача требует стратегического рассуждения |
| **Сложный анализ** | `worker-research` | `worker-review` | Задача с большим контекстом, требует synthesis |

### 2.2 Алгоритм маршрутизации

```
1. Классифицировать задачу по типу (NL-эвристика)
2. Определить первичный профиль из матрицы
3. Проверить health первичного профиля
4. Если health OK → delegate_task(profile=primary, ...)
5. Если health DEGRADED/OFFLINE → проверить fallback
6. Если fallback OK → delegate_task(profile=secondary, ...)
7. Если оба недоступны → выполнить задачу в default с предупреждением
```

Маршрутизация MUST учитывать capabilities профиля: если задача требует `browser`, а `worker-fast` не имеет этого инструмента, маршрутизация не должна выбирать этот профиль.

## 3. Fallback-цепочки

### 3.1 Модель fallback'а

При отказе провайдера (rate limit, timeout, model unavailable) Hermes использует внутренний механизм credential pools (см. `CREDENTIAL_POOLS.md`). На уровне оркестратора реализуется дополнительный fallback:

```
worker-code (kimi-k2.7-code) → [ОТКАЗ]
  ├──→ worker-fast (grok-4.5)     — быстрая альтернатива для кода
  ├──→ worker-code (deepseek-v4-pro, nvidia) — та же роль, другой провайдер
  └──→ default (deepseek-v4-pro)  — выполнить in-process
```

### 3.2 Стратегии fallback'а

| Стратегия | Описание | Применение |
|---|---|---|
| **Role-preserving** | Та же роль, другой провайдер | `worker-code` + `nvidia` вместо `opencode-go` |
| **Downgrade** | Более простой профиль | `worker-code` → `worker-fast` |
| **Escalate** | Более мощный профиль | `worker-fast` → `worker-code` |
| **In-process** | Выполнение в оркестраторе | Когда все worker'ы недоступны |

### 3.3 Политика повторных попыток

| Ошибка | Действие | Макс. повторов | Задержка |
|---|---|---|---|
| Rate limit (429) | Ждать + повторить тот же профиль | 3 | Exponential: 1s, 4s, 16s |
| Timeout (504) | Fallback на вторичный профиль | 1 | — |
| Model unavailable (503) | Fallback на вторичный профиль | 0 | — |
| Auth error (401/403) | Не повторять; alert оператору | 0 | — |
| Unknown error | Fallback → in-process | 1 | 5s |

## 4. Параллельное делегирование (Fan-out)

### 4.1 Паттерн

`delegate_task(tasks=[...])` запускает дочерние задачи параллельно:

```json
{
  "tasks": [
    {"goal": "Реализовать API endpoint /users", "profile": "worker-code"},
    {"goal": "Написать тесты для /users endpoint", "profile": "worker-code"},
    {"goal": "Обновить документацию API", "profile": "worker-fast"}
  ]
}
```

### 4.2 Ограничения

| Параметр | Значение по умолчанию | Описание |
|---|---|---|
| `max_concurrent_children` | 3 | Максимум параллельных дочерних задач |
| `max_spawn_depth` | 2 | Максимальная глубина вложенности оркестраторов |
| `max_iterations` | 50 | Максимум итераций на дочернюю задачу |

### 4.3 Сбор результатов

Оркестратор SHOULD:
1. Дождаться завершения всех дочерних задач (или таймаута)
2. Агрегировать результаты в порядке исходного списка
3. При частичном отказе — вернуть успешные результаты + ошибки для упавших
4. Предложить пользователю retry для упавших задач

## 5. Передача контекста

### 5.1 Механизмы

| Механизм | Формат | Применение |
|---|---|---|
| `goal` + `context` | Markdown/JSON | Основной механизм: цель + структурированный контекст |
| Файловая система | Файлы в рабочей директории | Общие артефакты (спецификации, результаты) |
| `memory` tool | MEMORY.md | Долгоживущие факты/решения между сессиями |
| `session_search` | FTS5-поиск | Поиск релевантной истории |

### 5.2 Формат контекста

```json
{
  "goal": "Реализовать модуль аутентификации",
  "context": {
    "objective": "JWT-based authentication module",
    "acceptance_criteria": ["Login endpoint", "Token refresh", "Password reset"],
    "constraints": {"framework": "FastAPI", "database": "PostgreSQL"},
    "decisions": ["Use python-jose for JWT", "Use passlib for hashing"],
    "artifact_refs": ["specs/auth-spec.md", "schemas/user.sql"],
    "completed_work": ["Database schema created", "User model defined"],
    "pending_work": ["Implement /login", "Implement /refresh"],
    "errors": []
  }
}
```

## 6. Health-check worker-профилей

### 6.1 Процедура

Health-check MUST выполняться:
- Перед каждой делегацией задачи
- Периодически (раз в 5 минут) для фонового мониторинга

```bash
# Проверка конкретного профиля
hermes --profile worker-code chat -q "respond with 'OK'" --quiet

# Проверка статуса провайдера
hermes --profile worker-code doctor
```

### 6.2 Состояния

| Состояние | Критерий | Действие |
|---|---|---|
| `ONLINE` | Успешный ping < 5s | Нормальная маршрутизация |
| `DEGRADED` | Успешный ping, но > 5s или retries | Маршрутизация с предупреждением, приоритет fallback |
| `OFFLINE` | Ping failed / timeout 30s | Исключить из маршрутизации, алерт оператору |
| `INCOMPATIBLE` | Adapter version mismatch | Заблокировать запуск, требуется upgrade |

### 6.3 Метрики health-check

| Метрика | Порог WARNING | Порог CRITICAL |
|---|---|---|
| Ping latency | > 5s | > 30s (timeout) |
| Error rate (5 min) | > 10% | > 25% |
| Token usage rate | > 80% квоты | > 95% квоты |
| Active runs | > 5 | > 10 |

## 7. Паттерны обработки ошибок

### 7.1 Классификация ошибок делегирования

| Код | Ошибка | Действие |
|---|---|---|
| `DELEGATION_TIMEOUT` | Дочерняя задача превысила `max_iterations` | Возврат частичного результата; предложить разбить задачу |
| `DELEGATION_PROFILE_OFFLINE` | Профиль недоступен | Fallback на альтернативный профиль |
| `DELEGATION_RATE_LIMITED` | Исчерпана квота провайдера | Fallback на профиль с другим провайдером |
| `DELEGATION_TOOL_ERROR` | Ошибка инструмента в дочерней задаче | Повтор с уточнённым контекстом |
| `DELEGATION_DEPTH_EXCEEDED` | Превышена `max_spawn_depth` | Выполнить задачу in-process |

### 7.2 Таймауты

| Стадия | Таймаут по умолчанию | Описание |
|---|---|---|
| Запуск профиля | 10s | Время на инициализацию Hermes |
| Ответ на goal | 60s | Время до первого осмысленного ответа |
| Полное выполнение | 300s (5 min) | Общее время на задачу |
| Сбор результатов | 30s | Таймаут после завершения задачи |

## 8. Ссылки

- [HERMES.md](../adapters/HERMES.md) — спецификация Hermes-адаптера
- [SPECIFICATION.md](../SPECIFICATION.md) §6.4 — Runs, approvals и handoff
- [ARCHITECTURE.md](../ARCHITECTURE.md) §5 — Run и handoff state machine
- [CREDENTIAL_POOLS.md](CREDENTIAL_POOLS.md) — управление пулами ключей
- [MONITORING.md](../operations/MONITORING.md) — мониторинг health-check'ов
