from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    repo_path TEXT NOT NULL,
    memory_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('REGISTERED','WAITING','ACTIVE','PAUSED','FAILED')),
    priority INTEGER NOT NULL DEFAULT 100,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    acceptance_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL CHECK(status IN ('QUEUED','DEV','TEST','REWORK','REVIEW','AUDIT','DONE','FAILED','ESCALATED')),
    priority INTEGER NOT NULL DEFAULT 100,
    attempt INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workers (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    account_ref TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('READY','BUSY','DRAINING','COOLDOWN','OFFLINE','DISABLED')),
    capabilities_json TEXT NOT NULL DEFAULT '{}',
    max_concurrency INTEGER NOT NULL DEFAULT 1,
    quota_reset_at TEXT,
    last_heartbeat TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leases (
    id TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL REFERENCES workers(id),
    project_id TEXT NOT NULL REFERENCES projects(id),
    task_id TEXT NOT NULL REFERENCES tasks(id),
    role TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    released_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS one_live_lease_per_worker
ON leases(worker_id) WHERE released_at IS NULL;

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    project_id TEXT,
    task_id TEXT,
    worker_id TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS dispatch_runs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    task_id TEXT NOT NULL REFERENCES tasks(id),
    worker_id TEXT NOT NULL REFERENCES workers(id),
    lane TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('RUNNING','SUCCEEDED','FAILED','TIMED_OUT')),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    exit_code INTEGER,
    output_tail TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS scheduler_state (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            self._migrate(conn)

    @staticmethod
    def _migrate(conn: sqlite3.Connection) -> None:
        """Apply additive migrations to databases created by the passive controller."""
        task_columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
        additions = {
            "external_ref": "TEXT",
            "lane": "TEXT",
            "source_path": "TEXT",
            "last_error": "TEXT",
        }
        for name, declaration in additions.items():
            if name not in task_columns:
                conn.execute(f"ALTER TABLE tasks ADD COLUMN {name} {declaration}")
        conn.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS one_external_task_per_project
               ON tasks(project_id, external_ref) WHERE external_ref IS NOT NULL"""
        )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()
