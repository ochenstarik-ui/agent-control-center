#!/usr/bin/env python3
"""Structural validator for Agent Control Center specification documents."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "SPECIFICATION.md"
ARCH = ROOT / "docs" / "ARCHITECTURE.md"
RESEARCH = ROOT / "docs" / "RESEARCH.md"
QUESTIONS = ROOT / "docs" / "OPEN-QUESTIONS.md"
TRACEABILITY = ROOT / "docs" / "TRACEABILITY.md"
README = ROOT / "README.md"
VALIDATOR = ROOT / "scripts" / "validate_spec.py"

REQUIRED_FILES = [
    SPEC,
    ARCH,
    RESEARCH,
    QUESTIONS,
    TRACEABILITY,
    README,
    VALIDATOR,
]
REQUIRED_SECTIONS = [
    "Назначение",
    "Не-цели MVP",
    "Пользователи и роли",
    "Функциональные требования",
    "Нефункциональные требования",
    "UI/UX specification",
    "API и event contract",
    "Data lifecycle",
    "Acceptance strategy",
    "Delivery plan",
    "Риски и меры",
    "Approval record",
]
REQ_RE = re.compile(r"\*\*((?:FR|NFR)-[A-Z]+-\d{3})\*\*")
AT_RE = re.compile(r"\*\*(AT-(?:FR|NFR)-[A-Z]+-\d{3})[:*]")
BLOCKER_RE = re.compile(r"\|\s*OQ-\d{3}\s*\|\s*BLOCKER\s*\|")
LOCAL_LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")


def fail(message: str) -> None:
    print(f"ERROR: {message}")


def main() -> int:
    errors = 0
    for path in REQUIRED_FILES:
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"missing or empty required file: {path.relative_to(ROOT)}")
            errors += 1

    if errors:
        return 1

    spec = SPEC.read_text(encoding="utf-8")
    questions = QUESTIONS.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        if section not in spec:
            fail(f"missing required section: {section}")
            errors += 1

    reqs = REQ_RE.findall(spec)
    ats = AT_RE.findall(spec)
    req_set = set(reqs)
    at_targets = {at.removeprefix("AT-") for at in ats}

    duplicates = sorted({req for req in reqs if reqs.count(req) > 1})
    duplicate_ats = sorted({at for at in ats if ats.count(at) > 1})
    if duplicates:
        fail(f"duplicate requirement IDs: {', '.join(duplicates)}")
        errors += 1
    if duplicate_ats:
        fail(f"duplicate acceptance test IDs: {', '.join(duplicate_ats)}")
        errors += 1

    missing_at = sorted(req_set - at_targets)
    orphan_at = sorted(at_targets - req_set)
    if missing_at:
        fail(f"requirements without acceptance test: {', '.join(missing_at)}")
        errors += 1
    if orphan_at:
        fail(f"acceptance tests without requirement: {', '.join(orphan_at)}")
        errors += 1

    for prefix, minimum in (("FR-", 35), ("NFR-", 20)):
        count = sum(req.startswith(prefix) for req in req_set)
        if count < minimum:
            fail(f"too few {prefix} requirements: {count} < {minimum}")
            errors += 1

    blockers = BLOCKER_RE.findall(questions)
    if not blockers:
        fail("OPEN-QUESTIONS.md must identify blocking decisions")
        errors += 1

    for markdown in ROOT.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for raw_target in LOCAL_LINK_RE.findall(text):
            target = raw_target.split("#", 1)[0]
            if target and not (markdown.parent / target).resolve().exists():
                fail(
                    f"broken local Markdown link in {markdown.relative_to(ROOT)}: "
                    f"{raw_target}"
                )
                errors += 1

    if "implementation blocked" not in spec.lower() or "implementation blocked" not in README.read_text(encoding="utf-8").lower():
        fail("draft implementation block must be explicit in spec and README")
        errors += 1

    if errors:
        print(f"FAIL: {errors} structural issue(s)")
        return 1

    print(
        "PASS: specification structure valid; "
        f"requirements={len(req_set)} (FR={sum(r.startswith('FR-') for r in req_set)}, "
        f"NFR={sum(r.startswith('NFR-') for r in req_set)}); "
        f"acceptance_tests={len(at_targets)}; blockers={len(blockers)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
