"""API для запуска задач на worker-профилях"""
from __future__ import annotations
import subprocess, uuid, json, os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

# In-memory storage (до БД в следующих частях)
_runs: dict[str, dict] = {}

HERMES = os.environ.get("HERMES_BIN", "hermes")

class RunRequest(BaseModel):
    agent: str = Field(description="worker-code | worker-fast | worker-research | worker-review")
    goal: str = Field(min_length=3, max_length=2000)
    model: str | None = None

class RunResponse(BaseModel):
    run_id: str
    agent: str
    goal: str
    status: str
    created_at: str

@router.post("", response_model=RunResponse)
def create_run(req: RunRequest):
    if req.agent not in ("worker-code", "worker-fast", "worker-research", "worker-review"):
        raise HTTPException(400, f"Неизвестный агент: {req.agent}")

    run_id = uuid.uuid4().hex[:12]
    created = datetime.now(timezone.utc).isoformat()
    cmd = [HERMES, "-p", req.agent, "chat", "-q", req.goal, "-Q"]
    if req.model:
        cmd.extend(["-m", req.model])

    # Запуск в фоне
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    _runs[run_id] = {
        "run_id": run_id, "agent": req.agent, "goal": req.goal,
        "status": "running", "created_at": created, "pid": process.pid,
    }
    return RunResponse(run_id=run_id, agent=req.agent, goal=req.goal, status="running", created_at=created)

@router.get("")
def list_runs(agent: str | None = None, limit: int = 20):
    result = list(_runs.values())
    if agent:
        result = [r for r in result if r["agent"] == agent]
    # Check status for running processes
    for r in result:
        if r["status"] == "running":
            try:
                pid = r.get("pid")
                if pid:
                    os.kill(pid, 0)  # check if alive
            except (OSError, ProcessLookupError):
                r["status"] = "completed"
    return {"runs": sorted(result, key=lambda r: r["created_at"], reverse=True)[:limit]}

@router.get("/{run_id}")
def get_run(run_id: str):
    if run_id not in _runs:
        raise HTTPException(404, "Задача не найдена")
    return _runs[run_id]
