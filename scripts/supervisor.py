#!/usr/bin/env python3
"""
Supervisor Agent — мониторинг и авто-переключение worker-профилей при отказе провайдеров.

Запуск:
  python scripts/supervisor.py
  или как cron: hermes cron create "*/5 * * * *" --script scripts/supervisor.py --no_agent

Конфигурация: supervisor.yaml (рядом с Hermes config)
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
CONFIG_PATH = HERMES_HOME / "supervisor.yaml"
INCIDENT_LOG = HERMES_HOME / "logs" / "supervisor.log"
STATE_FILE = HERMES_HOME / "cache" / "supervisor_state.json"

# ── Helpers ──────────────────────────────────────────────

def log(msg: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, file=sys.stderr)
    INCIDENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(INCIDENT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"incidents": [], "last_switch": {}, "last_check": {}}

def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))

def send_telegram(msg: str) -> None:
    """Отправить уведомление через hermes send (если настроен TELEGRAM_HOME_CHANNEL)"""
    try:
        subprocess.run(
            ["hermes", "send", "-t", "telegram", msg],
            capture_output=True, timeout=10
        )
    except Exception:
        pass  # telegram не настроен — не критично

# ── Config ───────────────────────────────────────────────

DEFAULT_CONFIG = {
    "check_interval": 300,
    "health_timeout": 15,
    "cooldown_minutes": 30,
    "api_key": "sk-a345af809e8a26f0693b9405344edc8adc5b5a96",  # 9Router key
    "health_url": "http://localhost:20127/v1/chat/completions",
    "notify_telegram": False,
    "providers": {
        "opencode-go": {"test_model": "opencode-go/kimi-k2.7-code"},
        "xai":         {"test_model": "xai/grok-4"},
        "gemini":      {"test_model": "gemini/gemini-3-flash-preview"},
        "nvidia":      {"test_model": "nvidia/deepseek-ai/deepseek-v4-pro"},
    },
    "fallback_matrix": {
        "worker-code": {
            "primary": "opencode-go/kimi-k2.7-code",
            "fallbacks": [
                "xai/grok-4",
                "nvidia/deepseek-ai/deepseek-v4-pro",
            ],
        },
        "worker-fast": {
            "primary": "xai/grok-4",
            "fallbacks": [
                "opencode-go/kimi-k2.7-code",
                "nvidia/deepseek-ai/deepseek-v4-pro",
            ],
        },
        "worker-research": {
            "primary": "gemini/gemini-3-flash-preview",
            "fallbacks": [
                "opencode-go/kimi-k2.7-code",
            ],
        },
        "worker-review": {
            "primary": "nvidia/deepseek-ai/deepseek-v4-pro",
            "fallbacks": [
                "opencode-go/kimi-k2.7-code",
            ],
        },
    },
}

def load_config() -> dict:
    if CONFIG_PATH.exists():
        import yaml
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG

# ── Health Check ─────────────────────────────────────────

def check_provider(provider_id: str, test_model: str, config: dict) -> str:
    """Проверяет провайдер через 9Router health probe.
    Возвращает: ok, quota_exceeded, payment_required, error, timeout
    """
    body = json.dumps({
        "model": test_model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 1,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        config["health_url"],
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
    )

    try:
        resp = urllib.request.urlopen(req, timeout=config["health_timeout"])
        return "ok"
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return "quota_exceeded"
        if e.code == 402:
            return "payment_required"
        if e.code in (401, 403):
            return "auth_error"
        return f"http_{e.code}"
    except Exception:
        return "timeout"

# ── Profile Switching ────────────────────────────────────

def get_current_model(profile: str) -> Optional[str]:
    """Получить текущую модель профиля"""
    try:
        r = subprocess.run(
            ["hermes", "config", "get", "model.default", "-p", profile],
            capture_output=True, text=True, timeout=10,
        )
        return r.stdout.strip()
    except Exception:
        return None

def switch_profile_model(profile: str, model: str) -> bool:
    """Переключить модель профиля"""
    try:
        r = subprocess.run(
            ["hermes", "config", "set", "model.default", model, "-p", profile],
            capture_output=True, text=True, timeout=15,
        )
        return r.returncode == 0
    except Exception as e:
        log(f"  ERROR switching {profile}: {e}")
        return False

# ── Main ─────────────────────────────────────────────────

def main():
    config = load_config()
    state = load_state()
    now = datetime.now()

    if not config.get("enabled", True):
        return

    log("=== Supervisor check ===")

    # 1. Проверить всех провайдеров
    provider_status = {}
    for provider_id, pconfig in config["providers"].items():
        status = check_provider(provider_id, pconfig["test_model"], config)
        provider_status[provider_id] = status
        icon = "✅" if status == "ok" else "❌"
        log(f"  {icon} {provider_id}: {status}")

    # 2. Найти профили с упавшими провайдерами
    for profile_name, matrix in config["fallback_matrix"].items():
        primary_model = matrix["primary"]
        primary_provider = primary_model.split("/")[0]

        if provider_status.get(primary_provider, "ok") == "ok":
            continue  # провайдер жив

        # Проверить cooldown
        last_switch_ts = state["last_switch"].get(profile_name, 0)
        cooldown = config["cooldown_minutes"] * 60
        if isinstance(last_switch_ts, str):
            last_switch_ts = datetime.fromisoformat(last_switch_ts).timestamp()
        if now.timestamp() - last_switch_ts < cooldown:
            log(f"  ⏳ {profile_name}: в cooldown, пропускаю")
            continue

        # Искать рабочий fallback
        current_model = get_current_model(profile_name)
        log(f"  ⚠ {profile_name}: primary {primary_model} DOWN (current: {current_model})")

        for fallback_model in matrix["fallbacks"]:
            fb_provider = fallback_model.split("/")[0]
            if provider_status.get(fb_provider, "ok") == "ok":
                if current_model == fallback_model:
                    log(f"    ✓ уже на fallback {fallback_model}")
                    break

                if switch_profile_model(profile_name, fallback_model):
                    incident = {
                        "timestamp": now.isoformat(),
                        "profile": profile_name,
                        "from_model": primary_model,
                        "to_model": fallback_model,
                        "reason": provider_status[primary_provider],
                    }
                    state["incidents"].append(incident)
                    state["last_switch"][profile_name] = now.isoformat()
                    save_state(state)

                    msg = (
                        f"🔴 Supervisor: {profile_name}\n"
                        f"   {primary_model} → {fallback_model}\n"
                        f"   Причина: {provider_status[primary_provider]}"
                    )
                    log(f"    ✓ SWITCHED: {primary_model} → {fallback_model}")
                    if config.get("notify_telegram"):
                        send_telegram(msg)
                break
        else:
            log(f"    ❌ Нет доступных fallback для {profile_name}!")

    # 3. Проверить восстановление — если primary снова жив, вернуть
    for profile_name, matrix in config["fallback_matrix"].items():
        primary_model = matrix["primary"]
        primary_provider = primary_model.split("/")[0]
        current_model = get_current_model(profile_name)

        if current_model and current_model != primary_model and provider_status.get(primary_provider) == "ok":
            # Primary восстановился — проверить 3 раза
            ok_count = 0
            for _ in range(3):
                if check_provider(primary_provider, config["providers"][primary_provider]["test_model"], config) == "ok":
                    ok_count += 1
                time.sleep(2)

            if ok_count == 3:
                if switch_profile_model(profile_name, primary_model):
                    incident = {
                        "timestamp": now.isoformat(),
                        "profile": profile_name,
                        "from_model": current_model,
                        "to_model": primary_model,
                        "reason": "recovery",
                    }
                    state["incidents"].append(incident)
                    save_state(state)

                    msg = (
                        f"🟢 Supervisor: {profile_name}\n"
                        f"   {current_model} → {primary_model}\n"
                        f"   Причина: primary восстановлен"
                    )
                    log(f"  ✓ RECOVERED: {current_model} → {primary_model}")
                    if config.get("notify_telegram"):
                        send_telegram(msg)

    log("=== Check complete ===\n")

if __name__ == "__main__":
    main()
