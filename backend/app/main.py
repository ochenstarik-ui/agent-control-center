"""Agent Control Center — Control Plane API (FastAPI)."""
from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Agent Control Center", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
MEMORY_DIR = HERMES_HOME / "acc-memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

WORKER_PROFILES = ["worker-code", "worker-fast", "worker-research", "worker-review"]

runs_db: dict[str, dict[str, Any]] = {}
projects_db: list[dict[str, Any]] = [
    {"id": "proj-1", "key": "ACC", "name": "Agent Control Center", "status": "active"},
    {"id": "proj-2", "key": "OPS", "name": "Operations", "status": "active"},
]

UI_BUILD_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if UI_BUILD_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/ui", StaticFiles(directory=UI_BUILD_DIR, html=True), name="ui")


# ── Helpers ──────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hermes_memory_path() -> Path:
    return MEMORY_DIR / "MEMORY.md"


def read_memory() -> str:
    path = hermes_memory_path()
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_memory(content: str) -> None:
    hermes_memory_path().write_text(content, encoding="utf-8")


# ── Models ───────────────────────────────────────────────

class RunCreate(BaseModel):
    profile: str = Field(..., description="Worker profile, e.g. worker-code")
    prompt: str = Field(..., min_length=1)
    context: str | None = None


class RunOut(BaseModel):
    id: str
    profile: str
    prompt: str
    status: str
    created_at: str
    updated_at: str
    output: str | None = None
    error: str | None = None


class HealthOut(BaseModel):
    profile: str
    current_model: str | None
    provider: str | None
    status: str
    latency_ms: int | None = None


class MemoryPut(BaseModel):
    content: str


# ── Endpoints: runs ──────────────────────────────────────

@app.post("/api/v1/runs", response_model=RunOut)
def create_run(payload: RunCreate) -> dict[str, Any]:
    if payload.profile not in WORKER_PROFILES:
        raise HTTPException(status_code=422, detail=f"Unknown profile: {payload.profile}")

    run_id = str(uuid.uuid4())
    run = {
        "id": run_id,
        "profile": payload.profile,
        "prompt": payload.prompt,
        "status": "queued",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "output": None,
        "error": None,
    }
    runs_db[run_id] = run

    # Dispatch via hermes chat -q (fire-and-forget background-friendly sync here)
    command = ["hermes", "-p", payload.profile, "chat", "-q", payload.prompt]
    try:
        run["status"] = "running"
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
            encoding="utf-8",
            errors="replace",
        )
        run["output"] = result.stdout.strip() or "(empty response)"
        if result.returncode != 0:
            run["status"] = "failed"
            run["error"] = result.stderr.strip() or "hermes exit non-zero"
        else:
            run["status"] = "succeeded"
    except subprocess.TimeoutExpired:
        run["status"] = "failed"
        run["error"] = "hermes timeout after 300s"
    except Exception as exc:
        run["status"] = "failed"
        run["error"] = f"dispatch error: {exc}"
    run["updated_at"] = now_iso()
    return run


@app.get("/api/v1/runs")
def list_runs() -> dict[str, Any]:
    return {"data": list(runs_db.values()), "meta": {"request_id": str(uuid.uuid4())}}


@app.get("/api/v1/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    run = runs_db.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"data": run, "meta": {"request_id": str(uuid.uuid4())}}


@app.delete("/api/v1/runs/{run_id}")
def cancel_run(run_id: str) -> dict[str, Any]:
    run = runs_db.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run["status"] in ("succeeded", "failed", "cancelled"):
        raise HTTPException(status_code=409, detail=f"Run already terminal: {run['status']}")
    run["status"] = "cancelled"
    run["updated_at"] = now_iso()
    return {"data": run, "meta": {"request_id": str(uuid.uuid4())}}


# ── Endpoints: agents / health ───────────────────────────

@app.post("/api/v1/agents/health")
def agents_health() -> dict[str, Any]:
    health = []
    for profile in WORKER_PROFILES:
        current_model = None
        try:
            r = subprocess.run(
                ["hermes", "config", "get", "model.default", "-p", profile],
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_model = r.stdout.strip() or None
        except Exception:
            current_model = None

        provider = current_model.split("/")[0] if current_model else None
        status = "unknown"
        latency_ms = None
        try:
            start = datetime.now(timezone.utc)
            r = subprocess.run(
                ["hermes", "-p", profile, "chat", "-q", "hi"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            status = "ok" if r.returncode == 0 else "error"
        except subprocess.TimeoutExpired:
            status = "timeout"
            latency_ms = 15000
        except Exception:
            status = "offline"

        health.append(
            {
                "profile": profile,
                "current_model": current_model,
                "provider": provider,
                "status": status,
                "latency_ms": latency_ms,
            }
        )
    return {"data": health, "meta": {"request_id": str(uuid.uuid4())}}


# ── Endpoints: projects ──────────────────────────────────

@app.get("/api/v1/projects")
def list_projects() -> dict[str, Any]:
    return {"data": projects_db, "meta": {"request_id": str(uuid.uuid4())}}


# ── Endpoints: memory ────────────────────────────────────

@app.get("/api/v1/memory/{key}")
def get_memory(key: str) -> dict[str, Any]:
    if key != "global":
        raise HTTPException(status_code=404, detail="Only key='global' is supported in MVP")
    return {
        "data": {"key": key, "content": read_memory()},
        "meta": {"request_id": str(uuid.uuid4())},
    }


@app.put("/api/v1/memory/{key}")
def put_memory(key: str, payload: MemoryPut) -> dict[str, Any]:
    if key != "global":
        raise HTTPException(status_code=404, detail="Only key='global' is supported in MVP")
    write_memory(payload.content)
    return {
        "data": {"key": key, "content": payload.content, "updated_at": now_iso()},
        "meta": {"request_id": str(uuid.uuid4())},
    }


# ── Root / docs ──────────────────────────────────────────

@app.get("/api/v1/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
