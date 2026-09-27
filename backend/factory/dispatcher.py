from __future__ import annotations

import logging
import os
import signal
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .compat import BusinessPlatformAdapter, LaneWork
from .service import ConflictError, FactoryController

logging.basicConfig(
    level=os.environ.get("FACTORY_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("ai_factory.dispatcher")


class Dispatcher:
    def __init__(self) -> None:
        self.project_id = os.environ.get("FACTORY_PROJECT_ID", "business-platform")
        repo = Path(os.environ.get("FACTORY_REPO", "/srv/projects/Agent projects/business-platform"))
        launcher = Path(
            os.environ.get("FACTORY_LAUNCHER", str(repo / "agents/pair/cron/lane-run.sh"))
        )
        lanes = [item.strip() for item in os.environ.get("FACTORY_LANES", "pair,pair2,pair3,pair6").split(",") if item.strip()]
        self.controller = FactoryController(
            Path(os.environ.get("FACTORY_DB", "/srv/projects/ai-factory-state/runtime.db")),
            int(os.environ.get("FACTORY_MAX_ACTIVE_PROJECTS", "2")),
        )
        self.adapter = BusinessPlatformAdapter(repo, launcher, lanes)
        self.interval = max(30, int(os.environ.get("FACTORY_DISPATCH_INTERVAL", "300")))
        self.timeout = max(60, int(os.environ.get("FACTORY_RUN_TIMEOUT", "3600")))
        self.max_parallel = max(1, min(4, int(os.environ.get("FACTORY_MAX_DEV_TEST_PAIRS", "4"))))
        self.stopping = False

    def _ensure_worker(self, work: LaneWork) -> str:
        worker_id = f"compat-{work.lane}-{work.next_role}"
        self.controller.register_worker(
            worker_id,
            "antigravity-compat",
            "dynamic-account-pool",
            {"role": work.next_role, "lane": work.lane, "compatibility_adapter": True},
        )
        return worker_id

    def reconcile(self) -> list[tuple[LaneWork, dict]]:
        project = self.controller.get_project(self.project_id)
        if project["status"] != "ACTIVE":
            logger.info("project=%s status=%s dispatch skipped", self.project_id, project["status"])
            return []
        failures = self.adapter.preflight()
        if failures:
            raise RuntimeError("; ".join(failures))
        works = self.adapter.inspect(fetch=True)
        reconciled: list[tuple[LaneWork, dict]] = []
        for work in works:
            paper = self.adapter.read_task_paper(work)
            task = self.controller.upsert_external_task(
                self.project_id,
                work.external_ref,
                work.title,
                paper,
                work.lane,
                work.source_path,
                work.observed_status,
            )
            reconciled.append((work, task))
        return reconciled

    def _run_one(self, work: LaneWork, task: dict) -> None:
        if not work.next_role:
            return
        worker_id = self._ensure_worker(work)
        try:
            lease = self.controller.acquire_lease(
                worker_id,
                self.project_id,
                task["id"],
                work.next_role.upper(),
                self.timeout + 300,
            )
        except ConflictError as exc:
            logger.info("lane=%s role=%s not dispatched: %s", work.lane, work.next_role, exc)
            return
        run_id = self.controller.begin_dispatch_run(
            self.project_id, task["id"], worker_id, work.lane, work.next_role
        )
        logger.info("run=%s lane=%s role=%s started", run_id, work.lane, work.next_role)
        try:
            if work.next_role == "codex":
                self.controller.reconcile_task(task["id"], "DEV", "compatibility worker started")
            exit_code, output = self.adapter.execute(work, self.timeout)
            status = "SUCCEEDED" if exit_code == 0 else ("TIMED_OUT" if exit_code == 124 else "FAILED")
            self.controller.finish_dispatch_run(run_id, status, exit_code, output)
            logger.info("run=%s lane=%s role=%s status=%s", run_id, work.lane, work.next_role, status)
        except Exception as exc:
            self.controller.finish_dispatch_run(run_id, "FAILED", None, str(exc))
            logger.exception("run=%s failed", run_id)
        finally:
            try:
                self.controller.release_lease(lease["lease_id"])
            except Exception:
                logger.exception("lease=%s release failed", lease["lease_id"])

    def cycle(self) -> None:
        items = self.reconcile()
        executable = [(work, task) for work, task in items if work.next_role]
        if not executable:
            logger.info("no executable lane work")
            return
        with ThreadPoolExecutor(max_workers=self.max_parallel, thread_name_prefix="factory-lane") as pool:
            futures = [pool.submit(self._run_one, work, task) for work, task in executable[: self.max_parallel]]
            for future in as_completed(futures):
                future.result()
        # Capture review/rework transitions produced by completed workers.
        self.reconcile()

    def run_forever(self) -> None:
        failures = self.adapter.preflight()
        if failures:
            raise SystemExit("dispatcher preflight failed: " + "; ".join(failures))
        logger.info(
            "dispatcher started project=%s lanes=%s interval=%ss",
            self.project_id,
            ",".join(self.adapter.lanes),
            self.interval,
        )
        while not self.stopping:
            started = time.monotonic()
            try:
                self.cycle()
            except Exception:
                logger.exception("dispatcher cycle failed")
            remaining = max(1, self.interval - int(time.monotonic() - started))
            for _ in range(remaining):
                if self.stopping:
                    break
                time.sleep(1)


def main() -> None:
    dispatcher = Dispatcher()

    def stop(_signum, _frame) -> None:
        dispatcher.stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    dispatcher.run_forever()


if __name__ == "__main__":
    main()
