# Credential Pools & Multi-Account Management

**Версия:** 0.1.0-draft
**Дата:** 2026-07-20
**Статус:** Draft
**Зависит от:** `SPECIFICATION.md`, `ARCHITECTURE.md`, `docs/adapters/HERMES.md`

> Этот документ описывает паттерны управления пулами API-ключей для провайдеров ИИ-моделей. Реализация запрещена до G0/G1 и утверждения оператором.

## 1. Обзор

Credential Pool — механизм ротации нескольких API-ключей в рамках одного провайдера, обеспечивающий:
- Автоматический обход исчерпанных квот
- Round-robin распределение нагрузки
- Приоритетное использование ключей
- Прозрачный failover без ручного вмешательства

## 2. Архитектура credential pool

```
┌─────────────────────────────────────────────┐
│               Hermes Agent                   │
│  ┌───────────────────────────────────────┐  │
│  │         Credential Pool Manager       │  │
│  │  ┌─────────┐  ┌─────────┐  ┌───────┐ │  │
│  │  │ Key #1  │  │ Key #2  │  │ Key N │ │  │
│  │  │ (active)│  │ (active)│  │(spare)│ │  │
│  │  └────┬────┘  └────┬────┘  └───┬───┘ │  │
│  │       │            │           │     │  │
│  │       ▼            ▼           ▼     │  │
│  │   ┌──────────────────────────────┐   │  │
│  │   │      Provider API Backend    │   │  │
│  │   └──────────────────────────────┘   │  │
│  └───────────────────────────────────────┘  │
│                                               │
│  ┌───────────────────────────────────────┐   │
│  │       9Router (опционально)           │   │
│  │  • Round-robin распределение          │   │
│  │  • Quota tracking                     │   │
│  │  • OpenAI-формат трансляции           │   │
│  └───────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## 3. Hermes Auth Pools

### 3.1 Конфигурация

Hermes поддерживает несколько ключей на одного провайдера через `hermes auth`:

```bash
# Добавление ключа
hermes auth add opencode-go
hermes auth add fireworks
hermes auth add gemini
hermes auth add nvidia

# Просмотр пула
hermes auth list opencode-go
# Вывод:
# [0] sk-abc...xyz  active   quota: 85%
# [1] sk-def...uvw  active   quota: 42%
# [2] sk-ghi...rst  active   quota: 12%

# Ручной сброс exhausted-статуса
hermes auth reset opencode-go 2
```

### 3.2 Стратегии выбора ключа

| Стратегия | Алгоритм | Применение |
|---|---|---|
| **Round-robin** | Последовательный перебор активных ключей | Равномерное распределение нагрузки |
| **Priority-based** | Ключи с более высоким приоритетом используются первыми | primary/fallback сценарий |
| **Least-loaded** | Ключ с наименьшим процентом использованной квоты | Оптимизация использования квот |
| **Failover-only** | Второй ключ активируется только при отказе первого | Минимизация случайного использования дорогих ключей |

### 3.3 Primary/Fallback паттерн

```yaml
# ~/.hermes/auth.json (концептуально)
{
  "pools": {
    "opencode-go": {
      "keys": [
        {
          "id": "primary",
          "key": "sk-primary-...",
          "priority": 1,
          "quota_limit": 1000000,
          "status": "active"
        },
        {
          "id": "fallback",
          "key": "sk-fallback-...",
          "priority": 2,
          "quota_limit": 500000,
          "status": "active"
        }
      ],
      "strategy": "priority"
    }
  }
}
```

### 3.4 Статусы ключей

| Статус | Описание | Поведение |
|---|---|---|
| `active` | Ключ работает | Используется согласно стратегии |
| `exhausted` | Ключ исчерпал квоту | Автоматически исключается из ротации |
| `rate_limited` | Временный rate limit | Исключается на cooldown-период (60s) |
| `error` | Ошибка аутентификации | Исключается до ручного сброса |
| `disabled` | Ручное отключение | Никогда не используется |

### 3.5 Обработка ошибок

| HTTP-код | Интерпретация | Действие |
|---|---|---|
| 401 | Неверный ключ | `status=error`; alert |
| 403 | Доступ запрещён | `status=error`; alert |
| 429 | Rate limit | `status=rate_limited`; retry через cooldown |
| 429 + `x-ratelimit-remaining: 0` | Квота исчерпана | `status=exhausted`; переключение на следующий ключ |
| 500/502/503 | Серверная ошибка | Retry до 3 раз; затем fallback ключ |
| Timeout | Сетевой сбой | Retry 1 раз; затем fallback ключ |

## 4. Интеграция с 9Router

### 4.1 Назначение

9Router — внешний агрегатор API-ключей, обеспечивающий:
- Централизованное управление пулом ключей от разных аккаунтов
- Round-robin / weighted распределение запросов
- Отслеживание квот в реальном времени
- Трансляцию форматов запросов (не-OpenAI → OpenAI-совместимый)
- Единый endpoint для всех моделей

### 4.2 Конфигурация Hermes → 9Router

```yaml
# config.yaml
model:
  provider: opencode-go
  base_url: "https://9router.example.com/v1/opencode-go"  # Проксируется через 9Router
  api_key: "${NINEROUTER_API_KEY}"
```

```bash
# .env
NINEROUTER_API_KEY=nr-...
```

### 4.3 Паттерны использования

#### Round-robin через 9Router

```yaml
# 9Router конфигурация (на стороне 9Router)
pools:
  opencode-go:
    strategy: round-robin
    keys:
      - account: personal
        key: sk-personal-...
        weight: 1
      - account: team
        key: sk-team-...
        weight: 2
      - account: backup
        key: sk-backup-...
        weight: 1
```

#### Quota tracking

9Router отслеживает использование через:
- Response headers (`x-ratelimit-remaining`, `x-ratelimit-reset`)
- Собственный счётчик токенов из тела ответа
- Периодический опрос `/v1/usage` (если доступен)

При достижении 95% квоты ключ помечается `low`; при 100% — `exhausted` и исключается из ротации.

### 4.4 Отказоустойчивость

Если 9Router недоступен, Hermes MUST fallback на прямое подключение к провайдеру с локальным credential pool:

```
Hermes → [попытка] 9Router → [отказ]
       → [fallback] прямой endpoint провайдера + локальный пул ключей
```

## 5. Мониторинг квот

### 5.1 Метрики

| Метрика | Источник | Обновление |
|---|---|---|
| `tokens_used` | Response body `usage.total_tokens` | Каждый запрос |
| `tokens_remaining` | Response header `x-ratelimit-remaining` или локальный счётчик | Каждый запрос |
| `quota_percent` | `tokens_used / quota_limit * 100` | Каждый запрос |
| `request_count` | Локальный счётчик | Каждый запрос |
| `error_count` | HTTP status != 200 | Каждый запрос |
| `latency_p95` | Локальный замер | Скользящее окно 5 мин |

### 5.2 Пороги и алерты

| Порог | Условие | Действие |
|---|---|---|
| `WARNING` | `quota_percent > 80%` | Уведомление оператору |
| `CRITICAL` | `quota_percent > 95%` | Автоматический failover на следующий ключ + алерт |
| `EXHAUSTED` | `quota_percent >= 100%` | Исключение ключа из ротации + инцидент |
| `ERROR_BURST` | > 5 ошибок за 1 мин | Отключение ключа на 5 мин + алерт |

### 5.3 Автоматический failover

```
1. Текущий ключ получает 429 с x-ratelimit-remaining: 0
2. Pool Manager помечает ключ exhausted
3. Выбирается следующий ключ согласно стратегии
4. Запрос повторяется с новым ключом
5. Если все ключи exhausted → возврат ошибки оператору
6. Exhausted-ключи сбрасываются при наступлении reset time
```

## 6. Безопасность

| Требование | Реализация |
|---|---|
| Ключи NEVER в логах | Secret redaction (`security.redact_secrets`) включён по умолчанию |
| Ключи NEVER в коде | Хранятся только в `.env` или `auth.json` |
| Ключи NEVER в Git | `.gitignore` исключает `.env`, `auth.json` |
| Ротация без простоя | Добавление нового ключа в пул + сброс старого после grace period |
| Аудит использования | Все операции с ключами логируются через `audit` tool |

## 7. Процедуры

### 7.1 Добавление нового ключа

```bash
# 1. Добавить ключ в пул
hermes auth add opencode-go

# 2. Проверить статус
hermes auth list opencode-go

# 3. Проверить health с новым ключом
hermes --profile worker-code doctor

# 4. При необходимости настроить 9Router
# Обновить конфигурацию 9Router с новым ключом
```

### 7.2 Замена скомпрометированного ключа

```bash
# 1. Немедленно отозвать ключ на стороне провайдера
# 2. Пометить ключ как error в Hermes
hermes auth remove opencode-go 1  # индекс скомпрометированного ключа

# 3. Добавить новый ключ
hermes auth add opencode-go

# 4. Проверить, что старый ключ не используется
# Проверить логи аудита
```

### 7.3 Сброс exhausted-статуса

```bash
# После сброса квоты (начало нового billing period)
hermes auth reset opencode-go 0
hermes auth reset opencode-go 1
```

## 8. Ссылки

- [HERMES.md](../adapters/HERMES.md) — спецификация Hermes-адаптера
- [WORKER_ORCHESTRATION.md](WORKER_ORCHESTRATION.md) — оркестрация worker-профилей
- [MONITORING.md](../operations/MONITORING.md) — мониторинг квот и алерты
- [BACKUP.md](../operations/BACKUP.md) — бэкап конфигурации credential pools
- [SPECIFICATION.md](../SPECIFICATION.md) §6.8 — Usage, notifications и audit
