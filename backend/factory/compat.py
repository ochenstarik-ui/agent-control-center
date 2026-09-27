from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

SAFE_LANE = re.compile(r"^pair(?:[2-9][0-9]*)?$")
SECRET_PATTERNS = (
    re.compile(r"(?i)(token|secret|password|api[_-]?key)\s*[=:]\s*\S+"),
    re.compile(r"(?i)(authorization)\s*:\s*bearer\s+\S+"),
)


def redact(text: str) -> str:
    clean = text
    for pattern in SECRET_PATTERNS:
        clean = pattern.sub(lambda match: f"{match.group(1)}=<redacted>", clean)
    return clean


@dataclass(frozen=True)
class LaneWork:
    lane: str
    external_ref: str
    title: str
    source_path: str
    branch: str | None
    observed_status: str
    next_role: str | None


class BusinessPlatformAdapter:
    """Read the established Git task-paper protocol and invoke its lane adapter."""

    def __init__(self, repo_path: str | Path, launcher_path: str | Path, lanes: list[str]):
        self.repo_path = Path(repo_path).resolve()
        self.launcher_path = Path(launcher_path).resolve()
        self.lanes = tuple(self._validate_lane(lane) for lane in lanes)

    @staticmethod
    def _validate_lane(lane: str) -> str:
        if not SAFE_LANE.fullmatch(lane):
            raise ValueError(f"unsafe lane name: {lane}")
        return lane

    def preflight(self) -> list[str]:
        failures: list[str] = []
        if not (self.repo_path / ".git").exists():
            failures.append(f"not a git checkout: {self.repo_path}")
        if not self.launcher_path.is_file():
            failures.append(f"launcher missing: {self.launcher_path}")
        return failures

    def _git(self, *args: str, timeout: int = 60, check: bool = True) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo_path), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if check and result.returncode != 0:
            raise RuntimeError(redact(result.stderr.strip() or result.stdout.strip()))
        return result.stdout.strip()

    def fetch(self) -> None:
        self._git("fetch", "-q", "origin", "--prune", timeout=120)

    def _markdown_at(self, ref: str, directory: str) -> list[str]:
        output = self._git("ls-tree", "-r", "--name-only", ref, "--", directory, check=False)
        return sorted(path for path in output.splitlines() if path.endswith(".md"))

    def _branches(self, lane: str) -> list[str]:
        output = self._git(
            "for-each-ref",
            "--sort=-committerdate",
            "--format=%(refname:short)",
            f"refs/remotes/origin/{lane}/*",
            check=False,
        )
        return [line for line in output.splitlines() if line and not line.endswith("/HEAD")]

    def inspect_lane(self, lane: str) -> LaneWork | None:
        lane = self._validate_lane(lane)
        inbox_dir = f"agents/{lane}/coder-inbox"
        inbox = self._markdown_at("origin/main", inbox_dir)
        if not inbox:
            return None

        # One paper per lane is the established invariant. Sorting makes a
        # violated invariant deterministic and visible to reconciliation.
        source_path = inbox[0]
        file_name = Path(source_path).name
        external_ref = f"{lane}:{file_name}"
        title = Path(file_name).stem

        for branch in self._branches(lane):
            locations = {
                "done": self._markdown_at(branch, f"agents/{lane}/done"),
                "rework": self._markdown_at(branch, f"agents/{lane}/rework"),
                "review": self._markdown_at(branch, f"agents/{lane}/review"),
            }
            if any(Path(path).name == file_name for path in locations["done"]):
                return LaneWork(lane, external_ref, title, source_path, branch, "REVIEW", None)
            if any(Path(path).name == file_name for path in locations["rework"]):
                return LaneWork(lane, external_ref, title, source_path, branch, "REWORK", "codex")
            if any(Path(path).name == file_name for path in locations["review"]):
                return LaneWork(lane, external_ref, title, source_path, branch, "TEST", "test")

        return LaneWork(lane, external_ref, title, source_path, None, "QUEUED", "codex")

    def inspect(self, *, fetch: bool = True) -> list[LaneWork]:
        if fetch:
            self.fetch()
        return [work for lane in self.lanes if (work := self.inspect_lane(lane)) is not None]

    def read_task_paper(self, work: LaneWork) -> str:
        return self._git("show", f"origin/main:{work.source_path}", timeout=30)

    def execute(self, work: LaneWork, timeout_seconds: int) -> tuple[int, str]:
        if work.next_role not in {"codex", "test"}:
            raise ValueError(f"lane {work.lane} has no executable role")
        try:
            result = subprocess.run(
                ["bash", str(self.launcher_path), work.lane, work.next_role],
                cwd=self.repo_path,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            output = "\n".join(part for part in (result.stdout, result.stderr) if part)
            return result.returncode, redact(output)[-12000:]
        except subprocess.TimeoutExpired as exc:
            output = "\n".join(
                part.decode(errors="replace") if isinstance(part, bytes) else (part or "")
                for part in (exc.stdout, exc.stderr)
            )
            return 124, redact(output + "\nexecution timed out")[-12000:]
