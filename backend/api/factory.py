from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from factory.service import ConflictError, FactoryController, NotFoundError

router = APIRouter(prefix="/api/v1/factory", tags=["factory"])
controller = FactoryController(
    Path(os.environ.get("FACTORY_DB", "/var/lib/ai-factory/runtime.db")),
    int(os.environ.get("FACTORY_MAX_ACTIVE_PROJECTS", "2")),
)


class ProjectRequest(BaseModel):
    project_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    name: str
    repo_path: str
    memory_path: str
    priority: int = 100


class TaskRequest(BaseModel):
    project_id: str
    title: str
    description: str
    acceptance: list[str] = Field(default_factory=list)
    priority: int = 100


class TransitionRequest(BaseModel):
    target: str
    reason: str = ""


class WorkerRequest(BaseModel):
    worker_id: str
    provider_id: str
    account_ref: str
    capabilities: dict = Field(default_factory=dict)
    max_concurrency: int = Field(default=1, ge=1, le=16)


class LeaseRequest(BaseModel):
    worker_id: str
    project_id: str
    task_id: str
    role: str
    ttl_seconds: int = Field(default=900, ge=30, le=86400)


def call(method, *args, **kwargs):
    try:
        return method(*args, **kwargs)
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/status")
def status():
    return controller.status()


@router.post("/projects")
def register_project(req: ProjectRequest):
    return call(controller.register_project, req.project_id, req.name, req.repo_path, req.memory_path, req.priority)


@router.post("/projects/{project_id}/activate")
def activate_project(project_id: str):
    return call(controller.activate_project, project_id)


@router.post("/projects/{project_id}/pause")
def pause_project(project_id: str):
    return call(controller.pause_project, project_id)


@router.get("/projects/{project_id}/bootstrap")
def bootstrap(project_id: str):
    return call(controller.bootstrap, project_id)


@router.post("/tasks")
def create_task(req: TaskRequest):
    return call(controller.create_task, req.project_id, req.title, req.description, req.acceptance, req.priority)


@router.post("/tasks/{task_id}/transition")
def transition_task(task_id: str, req: TransitionRequest):
    return call(controller.transition_task, task_id, req.target, req.reason)


@router.post("/workers")
def register_worker(req: WorkerRequest):
    call(controller.register_worker, req.worker_id, req.provider_id, req.account_ref, req.capabilities, req.max_concurrency)
    return {"worker_id": req.worker_id, "status": "READY"}


@router.post("/leases")
def acquire_lease(req: LeaseRequest):
    return call(controller.acquire_lease, req.worker_id, req.project_id, req.task_id, req.role, req.ttl_seconds)


@router.delete("/leases/{lease_id}")
def release_lease(lease_id: str):
    call(controller.release_lease, lease_id)
    return {"lease_id": lease_id, "released": True}
