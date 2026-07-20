from fastapi import APIRouter
from typing import List
from models import Task

router = APIRouter(prefix="/api/v1", tags=["tasks"])

tasks_db: List[Task] = [
    Task(id="t1", title="Реализовать EMA-кроссовер", description="Бэктест стратегии на Brent", status="in_progress", priority="high", assignee_agent_id="worker-code", project_id="p1"),
    Task(id="t2", title="Подготовить отчёт", description="Результаты бэктеста за Q3", status="todo", priority="medium", project_id="p1"),
    Task(id="t3", title="Настроить CI/CD", description="GitHub Actions для автотестов", status="review", priority="high", assignee_agent_id="worker-fast", project_id="p1"),
    Task(id="t4", title="Обновить вики", description="Документация по API", status="done", priority="low", project_id="p1"),
    Task(id="t5", title="Добавить OAuth", description="GitHub + Google интеграция", status="todo", priority="medium", project_id="p1"),
]

@router.get("/tasks", response_model=List[Task])
async def get_tasks():
    return tasks_db

@router.post("/tasks", response_model=Task)
async def create_task(task: Task):
    tasks_db.append(task)
    return task

@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, update: dict):
    for task in tasks_db:
        if task.id == task_id:
            for key, val in update.items():
                if hasattr(task, key):
                    setattr(task, key, val)
            return task
    return {"error": "Task not found"}
