# Supervisor Agent — надзиратель провайдеров

**Версия:** 0.1.0-draft | **Статус:** Draft

## Назначение

Supervisor Agent — специализированный агент-надзиратель, который:
1. Мониторит здоровье всех провайдеров/моделей
2. Обнаруживает исчерпание квот (429, 402, 403)
3. Переключает worker-профили на fallback-модели
4. Возвращает профили на основные модели после восстановления квот
5. Ведёт лог всех инцидентов и переключений

## Архитектура

```
Supervisor Agent (cron: каждые 5 мин)
  │
  ├─ check_provider(provider) → status
  │    ├─ HTTP health probe
  │    ├─ quota check (usage API)
  │    └─ latency check
  │
  ├─ detect_incident(status) → action
  │    ├─ 429 → switch to fallback
  │    ├─ 402 → switch to fallback
  │    ├─ timeout → mark degraded
  │    └─ recovery → switch back to primary
  │
  ├─ apply_action(profile, new_model)
  │    └─ hermes config set model.default <new_model> -p <profile>
  │
  └─ log_incident(incident)
       └─ supervisor.log + Telegram notification
```

## Модель инцидента

```yaml
incident:
  id: uuid
  timestamp: ISO8601
  provider: opencode-go|grok-cli|gemini|nvidia|ollama
  model: kimi-k2.7-code
  error_code: 429|402|403|timeout
  action: switch_to_fallback|switch_back|alert_only
  profile_affected: worker-code|worker-fast|worker-research|worker-review
  old_model: opencode-go/kimi-k2.7-code
  new_model: grok-cli/grok-4.5
  recovery_eta: "2026-07-21T00:00:00Z"
  status: active|resolved
```

## Матрица переключений

| Профиль | Primary | Fallback 1 | Fallback 2 | Last Resort |
|---------|---------|------------|------------|-------------|
| worker-code | opencode-go/kimi | grok-4.5 | gemini-3-flash | opencode-go (любая) |
| worker-fast | grok-4.5 | opencode-go/kimi | gemini-3-flash | opencode-go |
| worker-research | gemini-3-flash | opencode-go/kimi | grok-4.5 | opencode-go |
| worker-review | nvidia/deepseek-v4 | opencode-go/kimi | gemini-3-flash | opencode-go |

## Конфигурация supervisor

```yaml
# supervisor.yaml (рядом с Hermes config)
supervisor:
  enabled: true
  check_interval: 300          # секунд (5 минут)
  health_timeout: 15           # секунд на health probe
  cooldown_minutes: 30         # не переключать чаще чем раз в 30 мин
  notify:
    telegram: true
    log: true
  providers:
    opencode-go:
      health_url: http://localhost:20127/v1/models
      quota_reset: "daily"     # когда сбрасывается квота
    grok-cli:
      health_url: http://localhost:20127/v1/models
      quota_reset: "monthly"
    gemini:
      health_url: http://localhost:20127/v1/models
      quota_reset: "daily"
    nvidia:
      health_url: http://localhost:20127/v1/models
      quota_reset: "daily"
  fallback_matrix:
    worker-code:
      primary: opencode-go/kimi-k2.7-code
      fallbacks:
        - grok-cli/grok-4.5
        - gemini/gemini-3-flash-preview
    worker-fast:
      primary: grok-cli/grok-4.5
      fallbacks:
        - opencode-go/kimi-k2.7-code
        - gemini/gemini-3-flash-preview
    worker-research:
      primary: gemini/gemini-3-flash-preview
      fallbacks:
        - opencode-go/kimi-k2.7-code
    worker-review:
      primary: nvidia/deepseek-ai/deepseek-v4-pro
      fallbacks:
        - opencode-go/kimi-k2.7-code
```

## Алгоритм работы

```
1. КАЖДЫЕ check_interval секунд:
   a. Для каждого провайдера: POST health_url → статус
   b. Если 429/402/403 → INCIDENT
   c. Если timeout × 3 → DEGRADED

2. ПРИ ИНЦИДЕНТЕ:
   a. Проверить cooldown — если последнее переключение < 30 мин назад → alert_only
   b. Найти все профили с этим провайдером как primary
   c. Для каждого: переключить на первый доступный fallback
   d. Записать incident в лог
   e. Уведомить в Telegram

3. ПРИ ВОССТАНОВЛЕНИИ:
   a. Проверить primary провайдер 3 раза с интервалом 60с
   b. Если все 3 проверки OK → вернуть профили на primary
   c. Обновить incident.status = resolved
```

## Реализация

### Как cron-задача Hermes

```bash
hermes cron create "*/5 * * * *" \
  --name "supervisor-health-check" \
  --script scripts/supervisor.py \
  --no_agent  # script-only, не тратит токены LLM
```

### supervisor.py (псевдокод)

```python
def check_provider(health_url, api_key):
    r = requests.post(health_url, headers={"Authorization": f"Bearer {api_key}"},
                      json={"model": "test", "messages": [{"role":"user","content":"Hi"}], "max_tokens":1})
    if r.status_code == 429:
        return "quota_exceeded"
    if r.status_code == 402:
        return "payment_required"
    if r.status_code != 200:
        return "error"
    return "ok"

def switch_profile(profile, model):
    subprocess.run(["hermes", "config", "set", "model.default", model, "-p", profile])

def main():
    for provider in config["providers"]:
        status = check_provider(provider["health_url"], API_KEY)
        if status != "ok":
            # Найти затронутые профили и переключить
            for profile, fb in config["fallback_matrix"].items():
                if fb["primary"].startswith(provider):
                    for fallback_model in fb["fallbacks"]:
                        if check_provider(...) == "ok":
                            switch_profile(profile, fallback_model)
                            notify_telegram(f"{profile}: {fb['primary']} → {fallback_model}")
                            break
```

## Интеграция с Agent Control Center

Supervisor Agent — это Connector типа `hermes-cron` с адаптером `supervisor`.
В терминах ACC:
- **Agent:** supervisor (runtime: hermes-cron, model: none — script-only)
- **Capabilities:** provider_health_check, profile_switch, incident_logging
- **Connector:** локальный (встроен в Hermes)
- **Approvals:** не требуются (переключение модели — низкий риск)
