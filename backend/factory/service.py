from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .db import Database


TASK_TRANSITIONS = {
    "QUEUED": {"DEV", "FAILED"},
    "DEV": {"TEST", "FAILED", "ESCALATED"},
    "TEST": {"REWORK", "REVIEW", "FAILED", "ESCALATED"},
    "REWORK": {"DEV", "FAILED", "ESCALATED"},
    "REVIEW": {"REWORK", "AUDIT", "FAILED"},
    "AUDIT": {"REWORK", "DONE", "FAILED"},
    "DONE": set(),
    "FAILED": {"QUEUED"},
    "ESCALATED": {"DEV", "FAILED"},
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConflictError(RuntimeError):
    pass


class NotFoundError(RuntimeError):
    pass


class FactoryController:
    def __init__(self, db_path: str | Path, max_active_projects: int = 2):
        self.db = Database(db_path)
        self.max_active_projects = max_active_projects

    def _event(self, conn, event_type: str, *, project_id=None, task_id=None, worker_id=None, payload=None):
        conn.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, now(), event_type, project_id, task_id, worker_id, json.dumps(payload or {}, ensure_ascii=False)),
        )

    def register_project(self, project_id: str, name: str, repo_path: str, memory_path: str, priority: int = 100):
        stamp = now()
        with self.db.transaction() as conn:
            conn.execute(
                """INSERT INTO projects(id,name,repo_path,memory_path,status,priority,created_at,updated_at)
                   VALUES(?,?,?,?, 'REGISTERED',?,?,?)
                   ON CONFLICT(id) DO UPDATE SET name=excluded.name, repo_path=excluded.repo_path,
                   memory_path=excluded.memory_path, priority=excluded.priority, updated_at=excluded.updated_at""",
                (project_id, name, repo_path, memory_path, priority, stamp, stamp),
            )
            self._event(conn, "project.registered", project_id=project_id)
        return self.get_project(project_id)

    def get_project(self, project_id: str):
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            if not row:
                raise NotFoundError(project_id)
            return dict(row)

    def activate_project(self, project_id: str):
        stamp = now()
        with self.db.transaction() as conn:
            row = conn.execute("SELECT status FROM projects WHERE id=?", (project_id,)).fetchone()
            if not row:
                raise NotFoundError(project_id)
            active = conn.execute("SELECT count(*) FROM projects WHERE status='ACTIVE' AND id<>?", (project_id,)).fetchone()[0]
            target = "ACTIVE" if active < self.max_active_projects else "WAITING"
            conn.execute("UPDATE projects SET status=?, updated_at=? WHERE id=?", (target, stamp, project_id))
            self._event(conn, f"project.{target.lower()}", project_id=project_id)
        return self.get_project(project_id)

    def pause_project(self, project_id: str):
        with self.db.transaction() as conn:
            if not conn.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone():
                raise NotFoundError(project_id)
            conn.execute("UPDATE projects SET status='PAUSED', updated_at=? WHERE id=?", (now(), project_id))
            self._event(conn, "project.paused", project_id=project_id)
            waiting = conn.execute("SELECT id FROM projects WHERE status='WAITING' ORDER BY priority, created_at LIMIT 1").fetchone()
            if waiting:
                conn.execute("UPDATE projects SET status='ACTIVE', updated_at=? WHERE id=?", (now(), waiting[0]))
                self._event(conn, "project.active", project_id=waiting[0], payload={"reason": "slot_released"})
        return self.get_project(project_id)

    def create_task(self, project_id: str, title: str, description: str, acceptance: list[str], priority: int = 100):
        project = self.get_project(project_id)
        if project["status"] not in {"ACTIVE", "WAITING", "REGISTERED"}:
            raise ConflictError(f"project {project_id} is {project['status']}")
        task_id, stamp = f"task-{uuid.uuid4().hex[:12]}", now()
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO tasks VALUES (?,?,?,?,?, 'QUEUED',?,0,?,?)",
                (task_id, project_id, title, description, json.dumps(acceptance, ensure_ascii=False), priority, stamp, stamp),
            )
            self._event(conn, "task.created", project_id=project_id, task_id=task_id)
        return self.get_task(task_id)

    def get_task(self, task_id: str):
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                raise NotFoundError(task_id)
            result = dict(row)
            result["acceptance"] = json.loads(result.pop("acceptance_json"))
            return result

    def transition_task(self, task_id: str, target: str, reason: str = ""):
        target = target.upper()
        with self.db.transaction() as conn:
            row = conn.execute("SELECT project_id,status,attempt FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                raise NotFoundError(task_id)
            if target not in TASK_TRANSITIONS[row["status"]]:
                raise ConflictError(f"invalid transition {row['status']} -> {target}")
            attempt = row["attempt"] + (1 if target == "DEV" else 0)
            conn.execute("UPDATE tasks SET status=?, attempt=?, updated_at=? WHERE id=?", (target, attempt, now(), task_id))
            self._event(conn, "task.transition", project_id=row["project_id"], task_id=task_id,
                        payload={"from": row["status"], "to": target, "reason": reason})
        return self.get_task(task_id)

    def register_worker(self, worker_id: str, provider_id: str, account_ref: str, capabilities: dict, max_concurrency: int = 1):
        stamp = now()
        with self.db.transaction() as conn:
            conn.execute(
                """INSERT INTO workers VALUES (?,?,?,'READY',?,?,NULL,?,?)
                   ON CONFLICT(id) DO UPDATE SET provider_id=excluded.provider_id,
                   account_ref=excluded.account_ref, capabilities_json=excluded.capabilities_json,
                   max_concurrency=excluded.max_concurrency, last_heartbeat=excluded.last_heartbeat,
                   updated_at=excluded.updated_at""",
                (worker_id, provider_id, account_ref, json.dumps(capabilities), max(1, max_concurrency), stamp, stamp),
            )
            self._event(conn, "worker.registered", worker_id=worker_id)

    def acquire_lease(self, worker_id: str, project_id: str, task_id: str, role: str, ttl_seconds: int = 900):
        lease_id, acquired = f"lease-{uuid.uuid4().hex[:12]}", datetime.now(timezone.utc)
        expires = acquired + timedelta(seconds=ttl_seconds)
        with self.db.transaction() as conn:
            conn.execute("UPDATE leases SET released_at=? WHERE released_at IS NULL AND expires_at<=?", (now(), now()))
            worker = conn.execute("SELECT status FROM workers WHERE id=?", (worker_id,)).fetchone()
            if not worker:
                raise NotFoundError(worker_id)
            if worker["status"] not in {"READY", "BUSY"}:
                raise ConflictError(f"worker {worker_id} is {worker['status']}")
            if conn.execute("SELECT 1 FROM leases WHERE worker_id=? AND released_at IS NULL", (worker_id,)).fetchone():
                raise ConflictError(f"worker {worker_id} already leased")
            conn.execute("INSERT INTO leases VALUES (?,?,?,?,?,?,?,NULL)",
                         (lease_id, worker_id, project_id, task_id, role, acquired.isoformat(), expires.isoformat()))
            conn.execute("UPDATE workers SET status='BUSY', updated_at=? WHERE id=?", (now(), worker_id))
            self._event(conn, "lease.acquired", project_id=project_id, task_id=task_id, worker_id=worker_id,
                        payload={"lease_id": lease_id, "role": role})
        return {"lease_id": lease_id, "expires_at": expires.isoformat()}

    def release_lease(self, lease_id: str):
        with self.db.transaction() as conn:
            row = conn.execute("SELECT worker_id,project_id,task_id FROM leases WHERE id=? AND released_at IS NULL", (lease_id,)).fetchone()
            if not row:
                raise NotFoundError(lease_id)
            conn.execute("UPDATE leases SET released_at=? WHERE id=?", (now(), lease_id))
            conn.execute("UPDATE workers SET status='READY', updated_at=? WHERE id=?", (now(), row["worker_id"]))
            self._event(conn, "lease.released", project_id=row["project_id"], task_id=row["task_id"], worker_id=row["worker_id"], payload={"lease_id": lease_id})

    def bootstrap(self, project_id: str):
        project = self.get_project(project_id)
        with self.db.connect() as conn:
            tasks = [dict(r) for r in conn.execute("SELECT id,title,status,priority,attempt,updated_at FROM tasks WHERE project_id=? ORDER BY priority,created_at", (project_id,))]
            leases = [dict(r) for r in conn.execute("SELECT * FROM leases WHERE project_id=? AND released_at IS NULL AND expires_at>?", (project_id, now()))]
        return {"schema_version": 1, "project": project, "tasks": tasks, "active_leases": leases,
                "sources_of_truth": {"code": "git", "runtime": str(self.db.path), "memory": project["memory_path"], "secrets": "provider-local"}}

    def status(self):
        with self.db.connect() as conn:
            return {
                "projects": {r["status"]: r["count"] for r in conn.execute("SELECT status,count(*) count FROM projects GROUP BY status")},
                "tasks": {r["status"]: r["count"] for r in conn.execute("SELECT status,count(*) count FROM tasks GROUP BY status")},
                "workers": {r["status"]: r["count"] for r in conn.execute("SELECT status,count(*) count FROM workers GROUP BY status")},
                "active_leases": conn.execute("SELECT count(*) FROM leases WHERE released_at IS NULL AND expires_at>?", (now(),)).fetchone()[0],
                "max_active_projects": self.max_active_projects,
            }
