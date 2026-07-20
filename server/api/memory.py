"""API для работы с памятью (MEMORY.md)"""
from __future__ import annotations
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))

class MemoryEntry(BaseModel):
    key: str
    value: str

@router.get("/{key}")
def get_memory(key: str):
    path = HERMES_HOME / "memories" / "MEMORY.md"
    if not path.exists():
        return {"key": key, "value": None, "found": False}
    content = path.read_text(encoding="utf-8")
    # Поиск секции ключа
    for line in content.split("\n"):
        if key.lower() in line.lower():
            return {"key": key, "value": line.strip(), "found": True, "source": str(path)}
    return {"key": key, "value": None, "found": False}

@router.put("/{key}")
def set_memory(key: str, entry: MemoryEntry):
    path = HERMES_HOME / "memories" / "MEMORY.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    content += f"\n{entry.value}"
    path.write_text(content, encoding="utf-8")
    return {"status": "saved"}

@router.get("")
def list_memory(limit: int = 20):
    path = HERMES_HOME / "memories" / "MEMORY.md"
    if not path.exists():
        return {"entries": []}
    lines = [l.strip() for l in path.read_text(encoding="utf-8").split("\n") if l.strip() and not l.startswith("#")]
    return {"entries": [{"line": l} for l in lines[:limit]], "total": len(lines)}
