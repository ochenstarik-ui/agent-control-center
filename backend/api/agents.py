"""Health-check и статус worker-профилей"""
from __future__ import annotations
import subprocess, json
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

PROFILES = ["worker-code", "worker-fast", "worker-research", "worker-review"]
API_KEY = "sk-a345af809e8a26f0693b9405344edc8adc5b5a96"
PROFILES = ["worker-code", "worker-fast", "worker-research", "worker-review", "grok"]

MODEL_MAP = {
    "worker-code": "opencode-go/kimi-k2.7-code",
    "worker-fast": "opencode-go/kimi-k2.7-code",
    "worker-research": "opencode-go/kimi-k2.7-code",
    "worker-review": "opencode-go/kimi-k2.7-code",
    "grok": "xai/grok-4",
}

def _check_provider(model: str) -> str:
    try:
        import urllib.request, urllib.error
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1, "stream": False}).encode()
        req = urllib.request.Request(HEALTH_URL, data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"})
        urllib.request.urlopen(req, timeout=30)
        return "ok"
    except urllib.error.HTTPError as e:
        return f"http_{e.code}"
    except Exception:
        return "timeout"

@router.get("/health")
def agents_health():
    result = {}
    for profile in PROFILES:
        model = MODEL_MAP[profile]
        status = _check_provider(model)
        result[profile] = {"model": model, "provider_status": status, "healthy": status == "ok"}
    return result

@router.get("/{agent_id}")
def agent_info(agent_id: str):
    if agent_id not in PROFILES:
        return {"error": "unknown agent"}
    return {"agent_id": agent_id, "model": MODEL_MAP[agent_id], "status": _check_provider(MODEL_MAP[agent_id])}
