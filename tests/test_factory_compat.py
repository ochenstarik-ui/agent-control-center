import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from factory.compat import BusinessPlatformAdapter, redact


class FakeAdapter(BusinessPlatformAdapter):
    def __init__(self, tmp_path, branch_location=None):
        repo = tmp_path / "repo"
        (repo / ".git").mkdir(parents=True)
        launcher = tmp_path / "lane-run.sh"
        launcher.write_text("#!/bin/sh\n", encoding="utf-8")
        super().__init__(repo, launcher, ["pair"])
        self.branch_location = branch_location

    def _git(self, *args, timeout=60, check=True):
        if args[0] == "for-each-ref":
            return "origin/pair/task-1" if self.branch_location else ""
        if args[0] == "ls-tree":
            ref, directory = args[3], args[5]
            if ref == "origin/main" and directory == "agents/pair/coder-inbox":
                return "agents/pair/coder-inbox/TASK-1.md"
            if self.branch_location and ref == "origin/pair/task-1" and directory.endswith(self.branch_location):
                return f"agents/pair/{self.branch_location}/TASK-1.md"
            return ""
        if args[0] == "show":
            return "# TASK-1\n"
        return ""


def test_adapter_routes_new_paper_to_coder(tmp_path):
    work = FakeAdapter(tmp_path).inspect(fetch=False)[0]
    assert work.observed_status == "QUEUED"
    assert work.next_role == "codex"


def test_adapter_routes_review_to_tester(tmp_path):
    work = FakeAdapter(tmp_path, "review").inspect(fetch=False)[0]
    assert work.observed_status == "TEST"
    assert work.next_role == "test"


def test_adapter_stops_at_final_review(tmp_path):
    work = FakeAdapter(tmp_path, "done").inspect(fetch=False)[0]
    assert work.observed_status == "REVIEW"
    assert work.next_role is None


def test_dispatch_output_redacts_credentials():
    value = redact("token=abc password:secret Authorization: Bearer xyz")
    assert "abc" not in value
    assert "secret" not in value
    assert "xyz" not in value
