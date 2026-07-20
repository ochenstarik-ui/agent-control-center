"""API для скиллов"""
from __future__ import annotations
import os, json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))

@router.get("")
def list_skills():
    skills = []
    skills_dir = HERMES_HOME / "skills"
    if not skills_dir.exists():
        return {"skills": []}
    for d in sorted(skills_dir.iterdir()):
        if d.is_dir():
            md = d / "SKILL.md"
            if md.exists():
                content = md.read_text(encoding="utf-8", errors="replace")
                name = d.name
                category = ""
                for line in content.split("\n")[:10]:
                    if line.startswith("category:"):
                        category = line.split(":", 1)[1].strip()
                        break
                skills.append({"name": name, "category": category, "path": str(d)})
    return {"skills": skills}
