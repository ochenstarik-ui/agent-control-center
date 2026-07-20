# Hermes Agent Adapter Specification

**Версия:** 0.1.0-draft
**Дата:** 2026-07-20
**Статус:** Draft — implementation blocked
**Зависит от:** `SPECIFICATION.md` (§6.2 Connectors and agents), `ARCHITECTURE.md` (§4 Connector), `RESEARCH.md`

> Этот документ детализирует адаптер Hermes Agent в рамках Agent Adapter Protocol (AAP) согласно `SPECIFICATION.md`. Реализация запрещена до закрытия G0/G1 и явного утверждения оператором. Формулировки MUST/SHALL обязательны; SHOULD требуют обоснования отклонения.

## 1. Обзор

Hermes Agent — open-source фреймворк ИИ-агентов от Nous Research, работающий в терминале, desktop-приложении, мессенджерах и IDE. Адаптер ACC подключается через HTTP API Hermes (`/v1/chat/completions`, `/v1/responses`, `/v1/runs`) и использует систему профилей для изоляции рабочих нагрузок.

Hermes обеспечивает: provider-agnostic model routing, credential pools, профили, навыки (skills), память, cron, gateway (Telegram/20+ платформ), делегирование, сессионный поиск, tools (terminal, browser, file, code execution), плагины, MCP-серверы и webhook'и.

## 2. Профили

Hermes использует профили для изоляции независимых экземпляров агента. Каждый профиль имеет собственный `config.yaml`, `.env`, `skills/`, `plugins/`, `cron/` и `memories/`.

### 2.1 Базовый профиль

| Профиль | Назначение | Модель по умолчанию | Провайдер |
|---|---|---|---|
| `default` | Управляющий оркестратор | `deepseek-v4-pro` | `nvidia` |

Профиль `default` является точкой входа: принимает пользовательские запросы, маршрутизирует подзадачи worker-профилям через `delegate_task`, агрегирует результаты.

### 2.2 Worker-профили

| Профиль | Назначение | Модель | Провайдер | Типовые задачи |
|---|---|---|---|---|
| `worker-code` | Разработка и генерация кода | `kimi-k2.7-code` | `opencode-go` | Написание, рефакторинг, отладка кода; PR; code review |
| `worker-fast` | Быстрые задачи, не требующие глубокого анализа | `grok-4.5` | `fireworks` | Простые скрипты, форматирование, быстрый поиск |
| `worker-research` | Исследования и анализ | `gemini-3-flash-preview` | `gemini` | Анализ документации, исследование API, literature review |
| `worker-review` | Рецензирование и проверка качества | `deepseek-v4-pro` | `nvidia` | Code review, security audit, проверка спецификаций |

Каждый worker-профиль SHOULD иметь ограниченный набор инструментов, соответствующий его роли.

## 3. Модели и провайдеры

### 3.1 Модели

| Модель | Провайдер | Контекст (прибл.) | Назначение | Статус |
|---|---|---|---|---|
| `kimi-k2.7-code` | `opencode-go` | 128K | Генерация кода, сложный рефакторинг | Активен |
| `grok-4.5` | `fireworks` | 128K | Быстрые ответы, простые задачи | Активен |
| `gemini-3-flash-preview` | `gemini` | 1M | Исследования, анализ больших документов | Активен |
| `deepseek-v4-pro` | `nvidia` | 128K | Оркестрация, review, сложное рассуждение | Активен |

Модели резервируются: при недоступности одной моделью SHOULD срабатывать fallback-цепочка (см. `WORKER_ORCHESTRATION.md`).

### 3.2 Провайдеры

| Провайдер | Тип | Аутентификация | Env-переменная |
|---|---|---|---|
| `opencode-go` | OpenCode Go API | API key | `OPENCODE_GO_API_KEY` |
| `fireworks` | OpenAI-совместимый кастомный | API key | `FIREWORKS_API_KEY` |
| `gemini` | Google Gemini API | API key | `GOOGLE_API_KEY` или `GEMINI_API_KEY` |
| `nvidia` | NVIDIA AI API | API key | `NVIDIA_API_KEY` |
| `ollama` | Локальный | Без аутентификации | — |

**Custom OpenAI-совместимый провайдер (`fireworks`):** настраивается через `model.base_url` и `model.api_key` в `config.yaml`. Должен реализовывать `/v1/chat/completions` с поддержкой tool calling. Конфигурация:

```yaml
model:
  provider: fireworks
  base_url: "https://api.fireworks.ai/inference/v1"
  api_key: "${FIREWORKS_API_KEY}"
  model: grok-4.5
```

## 4. Инструменты

Hermes предоставляет следующие инструментальные наборы (toolsets), релевантные для адаптера:

| Инструмент | Назначение | Доступность в профилях |
|---|---|---|
| `terminal` | Выполнение shell-команд и управление процессами | Все профили |
| `browser` | Браузерная автоматизация (Chromium) | `default`, `worker-research` |
| `file` | Чтение/запись/поиск/редактирование файлов | Все профили |
| `delegation` | Делегирование подзадач sub-agent'ам | `default` (оркестратор) |
| `cronjob` | Управление запланированными задачами | `default` |
| `memory` | Персистентная память между сессиями | `default` |
| `session_search` | Поиск по истории сессий | `default` |
| `skills` | Просмотр и установка навыков | `default` |
| `gateway` | Управление gateway-сообщениями | `default` |
| `web` | Веб-поиск и извлечение контента | `default`, `worker-research` |
| `code_execution` | Песочница для выполнения Python | `worker-code` |

Worker-профили SHOULD иметь минимально необходимый набор инструментов для выполнения своей роли.

### 4.1 Делегирование (`delegate_task`)

`delegate_task` порождает sub-agent с изолированным контекстом и терминальной сессией.

**Параметры:**
- `goal` (обязательный) — цель подзадачи
- `context` — контекстная информация
- `role` — `leaf` (по умолчанию; не может ре-делегировать) или `orchestrator` (может порождать своих worker'ов)
- `background` — если `true`, возвращает handle немедленно
- `tasks` — массив задач для параллельного выполнения (fan-out)

**Ограничения:**
- `max_spawn_depth` (в `delegation` секции `config.yaml`) ограничивает глубину вложенности оркестраторов
- `max_concurrent_children` (по умолчанию 3) — максимум параллельных детей
- Максимальное количество итераций: `delegation.max_iterations` (по умолчанию 50)

**Важно:** делегирование не durable — дочерний процесс живёт в рамках родительского процесса. Для задач, которые должны пережить перезапуск, использовать `cronjob`.

## 5. Gateway

Hermes Gateway обеспечивает подключение к 20+ мессенджинг-платформам.

### 5.1 Telegram

| Параметр | Значение |
|---|---|
| Режим | Polling (long polling) |
| Fallback IPs | Поддерживаются альтернативные IP-адреса для обхода блокировок |
| Формат сообщений | MarkdownV2 / HTML |
| Доставка уведомлений | Через gateway adapter |
| Команды | `/approve`, `/deny`, `/restart`, `/sethome`, `/status`, `/agents` |

Настройка Telegram polling:

```yaml
gateway:
  platforms:
    telegram:
      token: "${TELEGRAM_BOT_TOKEN}"
      polling: true
      fallback_ips:
        - "149.154.167.220"
        - "149.154.167.50"
```

### 5.2 Поддерживаемые платформы

Discord, Slack, WhatsApp (Baileys + Business Cloud API), iMessage (Photon), Signal, Email, SMS, Matrix, Mattermost, Microsoft Teams, LINE, SimpleX, ntfy, Google Chat, Home Assistant, DingTalk, Feishu, WeCom, Weixin (WeChat), Raft, API Server, Webhooks.

Каждая платформа конфигурируется в секции `gateway.platforms.<name>`.

## 6. Cron

Планировщик Hermes поддерживает durable scheduled jobs.

### 6.1 Синтаксис расписаний

| Формат | Пример | Описание |
|---|---|---|
| Длительность | `"30m"`, `"2h"`, `"90s"` | Интервал между запусками |
| "Every"-фраза | `"every monday 9am"`, `"every 6 hours"` | Человеко-читаемое расписание |
| 5-полевой cron | `"0 9 * * *"` | Стандартный cron-синтаксис |
| ISO timestamp | `"2026-07-20T15:00:00Z"` | Однократный запуск |

### 6.2 Параметры задания

| Параметр | Описание |
|---|---|
| `skills` | Список навыков для загрузки |
| `model`/`provider` | Переопределение модели/провайдера |
| `script` | Pre-run скрипт сбора данных; `no_agent=True` делает скрипт единственным действием |
| `context_from` | Цепочка: вывод задания A → контекст задания B |
| `workdir` | Рабочая директория (загружает `AGENTS.md`/`CLAUDE.md` из неё при наличии) |
| Доставка | Multi-platform: Telegram, Email, Webhooks |

### 6.3 Инварианты

- 3-минутный hard interrupt на каждый run
- `.tick.lock` предотвращает дублирование тиков между процессами
- Cron-сессии передают `skip_memory=True` по умолчанию
- Доставка обрамляется header/footer, не зеркалируется в gateway-сессию

### 6.4 Watch patterns

При запуске через `terminal(background=True, watch_patterns=[...])` Hermes отслеживает вывод фонового процесса на совпадение с шаблонами. Rate limit: не более 1 уведомления в 15 секунд; после 3 последовательных окон с dropped matches отключается.

## 7. Skills (навыки)

Skills — переиспользуемые процедуры, сохраняемые агентом.

### 7.1 Жизненный цикл

```
create → use → idle → stale → archive
           ↑                  ↓
           └── restore ←──────┘
```

- Только навыки с `created_by: "agent"` подлежат автоматическому curator'у
- Bundled + hub-установленные навыки неприкосновенны
- Максимальное деструктивное действие — archive (никогда не delete)
- Pinned навыки исключены из всех авто-переходов

### 7.2 Curator

Фоновый процесс обслуживания навыков:

```bash
hermes curator status    # статус
hermes curator run       # ручной запуск
hermes curator pin NAME  # защита от авто-архивации
hermes curator archive NAME  # ручная архивация
hermes curator restore NAME  # восстановление
hermes curator backup    # создание снапшота
```

Consolidation (объединение пересекающихся навыков) **выключен по умолчанию** (`curator.consolidate: false`), требует aux-модель и явного включения.

### 7.3 Категории навыков

- **Встроенные** — поставляются с Hermes (code review, planning, TDD, debugging, и др.)
- **Пользовательские** — создаются агентом в процессе работы
- **Hub** — устанавливаются из реестра `hermes skills install`

## 8. Память

Hermes ведёт два файла памяти:

| Файл | Назначение |
|---|---|
| `MEMORY.md` | Факты, решения, уроки, выученные в процессе работы |
| `USER.md` | Предпочтения пользователя, окружение, постоянные параметры |

Память опционально может использовать внешние провайдеры (Honcho, Mem0) через `hermes memory setup`.

## 9. Конфигурация

### 9.1 config.yaml

Основной конфигурационный файл (`~/.hermes/config.yaml` или `$HERMES_HOME/config.yaml`). Ключевые секции для адаптера:

```yaml
model:
  default: deepseek-v4-pro
  provider: nvidia
  base_url: "https://integrate.api.nvidia.com/v1"

agent:
  max_turns: 90
  tool_use_enforcement: true

terminal:
  backend: local
  timeout: 180

delegation:
  model: kimi-k2.7-code
  provider: opencode-go
  max_iterations: 50
  max_spawn_depth: 2
  max_concurrent_children: 3

gateway:
  platforms:
    telegram:
      token: "${TELEGRAM_BOT_TOKEN}"
      polling: true

curator:
  enabled: true
  consolidate: false
  interval_hours: 24
  stale_after_days: 30
```

### 9.2 .env

Секреты и API-ключи:

```bash
OPENCODE_GO_API_KEY=sk-...
FIREWORKS_API_KEY=fw-...
GOOGLE_API_KEY=AIza...
NVIDIA_API_KEY=nvapi-...
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
```

### 9.3 Профили

Каждый профиль — изолированная директория `~/.hermes/profiles/<name>/` с собственными `config.yaml`, `.env`, `skills/`, `plugins/`, `cron/`, `memories/`.

Создание профиля:

```bash
hermes profile create worker-code
hermes profile create worker-fast
hermes profile create worker-research
hermes profile create worker-review
```

## 10. Возможности адаптера (capabilities)

При handshake с ACC адаптер Hermes публикует следующий набор capabilities:

| Capability | Значение | Примечание |
|---|---|---|
| `stream` | `true` | HTTP SSE / JSON Lines |
| `cancel` | `true` | Через `cancel` в run API |
| `checkpoint` | `true` | Observable checkpoint schema |
| `approvals` | `true` | Built-in approval flow |
| `tools` | `["terminal", "browser", "file", "web", "code_execution", ...]` | Зависит от профиля |
| `mcp` | `true` | MCP client support |
| `artifacts` | `true` | Файловая система + object refs |
| `usage_exact` | `false` | Hermes не предоставляет authoritative usage API |
| `usage_estimated` | `true` | Token usage из LLM-ответов |
| `filesystem_scope` | `["cwd", "home"]` | Ограничивается рабочей директорией |
| `structured_output` | `true` | JSON mode в моделях |
| `profiles` | `["default", "worker-code", "worker-fast", "worker-research", "worker-review"]` | Доступные профили |
| `resume` | `true` | Session resume через session ID |

## 11. Соответствие AAP

Адаптер Hermes реализует Agent Adapter Protocol (`ARCHITECTURE.md` §4.2):

| AAP-метод | Реализация в Hermes |
|---|---|
| `handshake()` | `GET /v1/status` → identity, version, capabilities |
| `health()` | `GET /v1/health` → status, latency, active_runs |
| `start(run_spec, context)` | `POST /v1/runs` → native_run_ref |
| `stream(run_ref, cursor)` | `GET /v1/runs/{id}/events?cursor=` → SSE |
| `checkpoint(run_ref, reason)` | `POST /v1/runs/{id}/checkpoint` → checkpoint bundle |
| `cancel(run_ref, mode)` | `POST /v1/runs/{id}/cancel` → outcome |
| `resume(run_ref)` | `POST /v1/runs/{id}/resume` → outcome |
| `usage(scope)` | `GET /v1/usage` → measured/estimated/unknown signal |
| `artifacts(run_ref)` | `GET /v1/runs/{id}/artifacts` → metadata + refs |

## 12. Ограничения и риски

| Ограничение | Влияние | Мера |
|---|---|---|
| Hermes не предоставляет authoritative usage API | Бюджетирование только estimated | Явная маркировка confidence; ручной budget policy |
| Делегирование не durable | Потеря задачи при падении родителя | Критичные задачи → cronjob |
| Worker-профили требуют отдельных процессов | Накладные расходы на запуск | Keep-warm пул worker'ов в production |
| Adapter версионирование отстаёт от Hermes | Incompatible handshake | Pinned version + contract tests + N-1 policy |
| Gateway polling подвержен сетевым сбоям | Задержка доставки | Fallback IPs, метрики polling latency |

## 13. Ссылки

- [Hermes Agent Documentation](https://hermes-agent.nousresearch.com/docs/)
- [Hermes API Server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server)
- [Hermes Profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles)
- [SPECIFICATION.md](../SPECIFICATION.md) — каноническое ТЗ ACC
- [ARCHITECTURE.md](../ARCHITECTURE.md) — архитектура ACC и AAP
- [RESEARCH.md](../RESEARCH.md) — исследование интеграций
- [WORKER_ORCHESTRATION.md](../patterns/WORKER_ORCHESTRATION.md) — паттерны оркестрации worker-профилей
- [CREDENTIAL_POOLS.md](../patterns/CREDENTIAL_POOLS.md) — паттерны credential pools
- [MONITORING.md](../operations/MONITORING.md) — мониторинг
- [BACKUP.md](../operations/BACKUP.md) — бэкап конфигурации
