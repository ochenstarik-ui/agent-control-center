import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from factory.service import ConflictError, FactoryController


@pytest.fixture
def factory(tmp_path):
    return FactoryController(tmp_path / "runtime.db", max_active_projects=2)


def add_project(factory, project_id):
    return factory.register_project(project_id, project_id, f"/repos/{project_id}", f"/memory/{project_id}")


def test_third_project_waits_and_is_promoted(factory):
    for project_id in ("project-a", "project-b", "project-c"):
        add_project(factory, project_id)
    assert factory.activate_project("project-a")["status"] == "ACTIVE"
    assert factory.activate_project("project-b")["status"] == "ACTIVE"
    assert factory.activate_project("project-c")["status"] == "WAITING"
    factory.pause_project("project-a")
    assert factory.get_project("project-c")["status"] == "ACTIVE"


def test_task_state_machine_rejects_skips(factory):
    add_project(factory, "business-platform")
    factory.activate_project("business-platform")
    task = factory.create_task("business-platform", "Work", "Description", ["tests green"])
    with pytest.raises(ConflictError):
        factory.transition_task(task["id"], "DONE")
    for state in ("DEV", "TEST", "REVIEW", "AUDIT", "DONE"):
        task = factory.transition_task(task["id"], state)
    assert task["status"] == "DONE"


def test_worker_cannot_be_leased_by_two_projects(factory):
    for project_id in ("project-a", "project-b"):
        add_project(factory, project_id)
        factory.activate_project(project_id)
    task_a = factory.create_task("project-a", "A", "A", [])
    task_b = factory.create_task("project-b", "B", "B", [])
    factory.register_worker("agy-codex", "antigravity", "account-ref", {"coding": 1.0})
    lease = factory.acquire_lease("agy-codex", "project-a", task_a["id"], "DEV")
    with pytest.raises(ConflictError):
        factory.acquire_lease("agy-codex", "project-b", task_b["id"], "DEV")
    factory.release_lease(lease["lease_id"])
    assert factory.acquire_lease("agy-codex", "project-b", task_b["id"], "DEV")


def test_bootstrap_is_complete_and_persistent(factory, tmp_path):
    add_project(factory, "business-platform")
    factory.activate_project("business-platform")
    task = factory.create_task("business-platform", "Finish platform", "Continue", ["CI green"])
    restarted = FactoryController(tmp_path / "runtime.db")
    boot = restarted.bootstrap("business-platform")
    assert boot["project"]["status"] == "ACTIVE"
    assert boot["tasks"][0]["id"] == task["id"]
    assert boot["sources_of_truth"]["code"] == "git"
