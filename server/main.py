"""
Agent Control Center — Control Plane API
Часть 1: управление агентами, задачами, памятью
Часть 2: Web UI
"""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import runs, agents, memory, skills, connectors

app = FastAPI(
    title="Agent Control Center",
    version="0.1.0",
    description="Control Plane для управления Hermes-агентами",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(runs.router)
app.include_router(agents.router)
app.include_router(memory.router)
app.include_router(skills.router)
app.include_router(connectors.router)

# Web UI (доступен на /ui)
static = Path(__file__).parent / "static"
static.mkdir(exist_ok=True)
app.mount("/ui", StaticFiles(directory=str(static), html=True), name="static")

@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}
