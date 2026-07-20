# Monitoring & Health-check

**Версия:** 0.1.0-draft
**Дата:** 2026-07-20
**Статус:** Draft
**Зависит от:** `SPECIFICATION.md` (§7.5 Operations and observability), `docs/adapters/HERMES.md`, `docs/patterns/WORKER_ORCHESTRATION.md`

> Этот документ описывает систему мониторинга и health-check'ов для Hermes Agent в составе Agent Control Center. Реализация запрещена до G0/G1 и утверждения оператором.

## 1. Обзор

Система мониторинга ACC охватывает три слоя:
1. **Инфраструктурный** — Connector, Control Plane, базы данных, сеть
2. **Агентский** — Hermes профили, провайдеры, credential pools
3. **Интеграционный** — Gateway (Telegram polling), 9Router, внешние API

## 2. Health-check компонентов

### 2.1 Матрица health-check

| Компонент | Метод проверки | Периодичность | Критичность |
|---|---|---|---|
| **Hermes default профиль** | `hermes --profile default doctor` | 5 мин | CRITICAL |
| **Worker-code** | `hermes --profile worker-code doctor` | 5 мин | HIGH |
| **Worker-fast** | `hermes --profile worker-fast doctor` | 5 мин | HIGH |
| **Worker-research** | `hermes --profile worker-research doctor` | 5 мин | MEDIUM |
| **Worker-review** | `hermes --profile worker-review doctor` | 5 мин | MEDIUM |
| **Gateway (Telegram)** | `hermes gateway status` | 1 мин | CRITICAL |
| **9Router** | `curl https://9router.example.com/health` | 1 мин | HIGH |
| **OpenCode Go API** | `curl -I https://api.opencode.ai/health` | 5 мин | HIGH |
| **Fireworks API** | `curl -I https://api.fireworks.ai/health` | 5 мин | HIGH |
| **Gemini API** | `curl -I https://generativelanguage.googleapis.com` | 5 мин | HIGH |
| **NVIDIA API** | `curl -I https://integrate.api.nvidia.com/v1` | 5 мин | HIGH |
| **Дисковое пространство** | `df -h` | 15 мин | MEDIUM |
| **Память** | `free -m` | 15 мин | MEDIUM |
| **CPU** | `top -bn1` | 15 мин | LOW |

### 2.2 Hermes Health-check

```bash
# Комплексная проверка
hermes doctor --fix

# Проверка конфигурации
hermes config check

# Статус компонентов
hermes status --all

# Проверка конкретного профиля
hermes --profile worker-code doctor

# Проверка gateway
hermes gateway status

# Проверка cron
hermes cron status
```

### 2.3 Интерпретация статусов

| Статус | Описание | SLA Impact |
|---|---|---|
| `healthy` | Все проверки пройдены | — |
| `degraded` | Часть функций работает с ограничениями | WARNING, частичная доступность |
| `unhealthy` | Критическая функция недоступна | CRITICAL, требуется intervention |
| `unknown` | Health-check не выполнен / нет данных | WARNING, проверка мониторинга |

## 3. Ключевые метрики

### 3.1 Latency

| Метрика | Цель | WARNING | CRITICAL |
|---|---|---|---|
| `hermes_response_time_p95` | ≤ 5s | > 10s | > 30s |
| `provider_latency_p95` (openrouter) | ≤ 3s | > 8s | > 20s |
| `delegate_task_startup_time_p95` | ≤ 10s | > 20s | > 60s |
| `telegram_polling_latency_p95` | ≤ 2s | > 5s | > 15s |
| `9router_proxy_latency_p95` | ≤ 500ms | > 2s | > 5s |

### 3.2 Token usage

| Метрика | Обновление | WARNING | CRITICAL |
|---|---|---|---|
| `tokens_used_daily` | Каждый запрос | > 80% дневной квоты | > 95% |
| `tokens_used_monthly` | Каждый запрос | > 80% месячной квоты | > 95% |
| `tokens_per_request_avg` | Скользящее окно 1 час | > 100K в среднем (аномалия) | > 500K (возможна утечка) |
| `cost_estimate_daily` | Ежечасно | > бюджета | > бюджета × 1.5 |

### 3.3 Error rates

| Метрика | Окно | WARNING | CRITICAL |
|---|---|---|---|
| `provider_4xx_rate` | 5 мин | > 5% | > 15% |
| `provider_5xx_rate` | 5 мин | > 2% | > 10% |
| `delegation_failure_rate` | 15 мин | > 10% | > 25% |
| `gateway_message_delivery_failure` | 15 мин | > 5% | > 15% |
| `telegram_polling_errors` | 5 мин | > 3 ошибок | > 10 ошибок |

### 3.4 Gateway метрики

| Метрика | Описание | WARNING | CRITICAL |
|---|---|---|---|
| `telegram_polling_loop_healthy` | polling loop активен | false в течение 2 мин | false в течение 5 мин |
| `gateway_websocket_connected` | mTLS WSS к Control Plane | disconnected > 30s | disconnected > 5 мин |
| `active_user_sessions` | Количество активных пользователей | = 0 (нет активности) | — |
| `message_queue_depth` | Глубина очереди недоставленных сообщений | > 100 | > 1000 |

## 4. Алерты

### 4.1 Классификация

| Severity | Описание | Время реакции | Эскалация |
|---|---|---|---|
| **CRITICAL** | Сервис недоступен, пользователи затронуты | 5 мин | Немедленно → Operator |
| **WARNING** | Деградация, возможны проблемы | 30 мин | В течение часа |
| **INFO** | Информационное событие | — | В рабочее время |

### 4.2 Перечень алертов

| Alert ID | Название | Severity | Условие | Runbook |
|---|---|---|---|---|
| `ALT-GTW-001` | Gateway down | CRITICAL | `hermes gateway status` != running | [§6.1](#61-gateway-down) |
| `ALT-GTW-002` | Telegram polling lag | WARNING | Polling latency > 5s за 5 мин | [§6.2](#62-telegram-polling-lag) |
| `ALT-PRV-001` | Provider quota exhausted | CRITICAL | Все ключи провайдера exhausted | [§6.3](#63-provider-quota-exhausted) |
| `ALT-PRV-002` | Provider unavailable | CRITICAL | Все провайдеры для профиля unhealthy | [§6.4](#64-provider-unavailable) |
| `ALT-PRV-003` | Quota warning | WARNING | > 80% квоты использовано | [§6.3](#63-provider-quota-exhausted) |
| `ALT-WRK-001` | Worker profile offline | WARNING | Профиль unhealthy > 10 мин | [§6.5](#65-worker-profile-offline) |
| `ALT-WRK-002` | All workers offline | CRITICAL | Все worker-профили unhealthy | [§6.5](#65-worker-profile-offline) |
| `ALT-CFG-001` | Config invalid | WARNING | `hermes config check` failed | [§6.6](#66-config-invalid) |
| `ALT-BKP-001` | Backup failed | WARNING | Последний снапшот старше 24ч | [BACKUP.md](BACKUP.md) |
| `ALT-DSK-001` | Low disk space | CRITICAL | < 5 GB свободно | [§6.7](#67-low-disk-space) |
| `ALT-9RT-001` | 9Router unreachable | WARNING | Health-check 9Router failed > 5 мин | [§6.8](#68-9router-unreachable) |
| `ALT-CRN-001` | Cron scheduler stalled | WARNING | Последний tick > 2× интервала | `hermes cron status` |

## 5. Мониторинговые инструменты

### 5.1 Встроенные

| Инструмент | Команда | Назначение |
|---|---|---|
| `hermes doctor` | `hermes doctor [--fix]` | Проверка зависимостей и конфигурации |
| `hermes status` | `hermes status --all` | Статус компонентов |
| `hermes config check` | `hermes config check` | Проверка конфигурации |
| `hermes gateway status` | `hermes gateway status` | Статус gateway |
| `hermes cron status` | `hermes cron status` | Статус планировщика |
| `hermes insights` | `hermes insights --days 7` | Аналитика использования |
| `hermes debug` | `hermes debug` (или `/debug`) | Отчёт для отладки |

### 5.2 Внешние (рекомендуемые)

- **Prometheus + Grafana** — сбор и визуализация метрик
- **Healthchecks.io / Uptime Kuma** — внешний мониторинг доступности
- **Sentry / Datadog** — отслеживание ошибок
- **W&B** — логирование ML-экспериментов и usage

## 6. Процедуры восстановления

### 6.1 Gateway down

```bash
# 1. Проверить статус
hermes gateway status

# 2. Проверить логи
tail -100 ~/.hermes/logs/gateway.log | grep -i "error\|failed"

# 3. Перезапустить
hermes gateway restart

# 4. Если не помогло — проверить systemd (Linux)
systemctl --user status hermes-gateway
systemctl --user reset-failed hermes-gateway
systemctl --user restart hermes-gateway

# 5. Если crash loop — проверить конфигурацию платформ
hermes config check
# Убедиться, что токены платформ валидны
```

### 6.2 Telegram polling lag

```bash
# 1. Проверить статус polling
hermes gateway status | grep telegram

# 2. Переключить fallback IP (если блокировка)
# В config.yaml:
# gateway.platforms.telegram.fallback_ips добавить/изменить IP

# 3. Перезапустить gateway
hermes gateway restart
```

### 6.3 Provider quota exhausted

```bash
# 1. Проверить статус ключей
hermes auth list opencode-go
hermes auth list fireworks
hermes auth list gemini
hermes auth list nvidia

# 2. Если есть активные ключи — проверить стратегию
# Убедиться, что exhausted ключи корректно исключены

# 3. Если все ключи exhausted:
#    a. Проверить наличие резервных ключей
#    b. Добавить новый ключ: hermes auth add <provider>
#    c. Или ждать сброса квоты

# 4. Для срочных задач — переключить на другого провайдера
#    worker-code (opencode-go) → worker-code (nvidia / deepseek-v4-pro)
```

### 6.4 Provider unavailable

```bash
# 1. Проверить доступность API
curl -I https://api.opencode.ai/health
curl -I https://api.fireworks.ai/health
curl -I https://generativelanguage.googleapis.com

# 2. Если API недоступен — ждать восстановления
# 3. Переключить профили на альтернативных провайдеров
#    (см. WORKER_ORCHESTRATION.md §3 Fallback-цепочки)

# 4. Проверить статус 9Router
curl https://9router.example.com/health
```

### 6.5 Worker profile offline

```bash
# 1. Проверить статус профиля
hermes --profile worker-code doctor

# 2. Проверить конфигурацию
hermes --profile worker-code config check

# 3. Проверить .env профиля
hermes --profile worker-code config env-path
# Убедиться, что API ключи на месте и валидны

# 4. Проверить доступность провайдера (см. §6.4)

# 5. Если проблема в модели — переключить модель
hermes --profile worker-code config set model.default <alternative_model>
```

### 6.6 Config invalid

```bash
# 1. Проверить синтаксис
hermes config check

# 2. Сравнить с последним бэкапом
diff ~/.hermes/config.yaml ~/.hermes/backups/latest/config.yaml

# 3. Восстановить из бэкапа (см. BACKUP.md)
python scripts/restore_backup.py --latest
```

### 6.7 Low disk space

```bash
# 1. Определить, что занимает место
du -sh ~/.hermes/sessions/
du -sh ~/.hermes/logs/
du -sh ~/.hermes/audio_cache/

# 2. Очистить старые сессии
hermes sessions prune --older-than 30

# 3. Очистить старые логи
find ~/.hermes/logs/ -name "*.log" -mtime +7 -delete

# 4. Очистить audio cache
find ~/.hermes/audio_cache/ -mtime +7 -delete
```

### 6.8 9Router unreachable

```bash
# 1. Проверить доступность
curl -v https://9router.example.com/health

# 2. Переключить Hermes на прямой endpoint
# В config.yaml изменить base_url на прямой URL провайдера
hermes config set model.base_url "https://api.opencode.ai/v1"

# 3. После восстановления 9Router — вернуть конфигурацию
```

## 7. Панель мониторинга

Рекомендуемая структура дашборда:

```
┌─────────────────────────────────────────────────────────┐
│  AGENT CONTROL CENTER — MONITORING          v0.1.0-draft │
├────────────┬────────────┬────────────┬──────────────────┤
│  PROFILES  │ PROVIDERS  │  GATEWAY   │  INFRASTRUCTURE  │
│  ────────  │  ────────  │  ────────  │  ──────────────  │
│  default   │ opencode   │ telegram   │  CPU:  34%       │
│  ● ONLINE  │ ● HEALTHY  │ ● ONLINE   │  RAM:  62%       │
│            │            │            │  DISK: 41%       │
│  worker-c  │ fireworks  │ discord    │                  │
│  ● ONLINE  │ ● DEGRADED │ ○ OFFLINE  │  UPTIME: 14d 3h  │
│            │            │            │                  │
│  worker-f  │ gemini     │ slack      │  CONNECTOR       │
│  ● ONLINE  │ ● HEALTHY  │ ○ OFFLINE  │  ● CONNECTED     │
│            │            │            │                  │
│  worker-r  │ nvidia     │            │  BACKUP          │
│  ● ONLINE  │ ● HEALTHY  │            │  ✓ 2h ago        │
│            │            │            │                  │
│  worker-rv │            │            │  CRON            │
│  ● ONLINE  │            │            │  ✓ running       │
├────────────┴────────────┴────────────┴──────────────────┤
│  USAGE TODAY                    ERRORS (LAST HOUR)       │
│  ─────────                      ──────────────────       │
│  Tokens: 1.2M / 5M (24%)        Total: 12               │
│  Cost:   $4.20 / $25.00 (17%)   4xx: 8  | 5xx: 4        │
│                                  Rate: 0.3%              │
├──────────────────────────────────────────────────────────┤
│  RECENT EVENTS                                           │
│  14:32  INFO   worker-code: task completed (45s)         │
│  14:30  WARN   fireworks: quota 82%                      │
│  14:28  INFO   telegram: message delivered               │
│  14:25  WARN   worker-fast: latency spike (8.2s p95)     │
└──────────────────────────────────────────────────────────┘
```

## 8. Ссылки

- [HERMES.md](../adapters/HERMES.md) — спецификация Hermes-адаптера
- [WORKER_ORCHESTRATION.md](../patterns/WORKER_ORCHESTRATION.md) — health-check worker-профилей
- [CREDENTIAL_POOLS.md](../patterns/CREDENTIAL_POOLS.md) — мониторинг квот
- [BACKUP.md](BACKUP.md) — бэкап и восстановление
- [SPECIFICATION.md](../SPECIFICATION.md) §7.5 — Operations and observability
