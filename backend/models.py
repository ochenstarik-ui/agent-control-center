from pydantic import BaseModel
from typing import Literal, Optional

class Agent(BaseModel):
    id: str
    name: str
    status: Literal["online", "offline", "busy"] = "online"
    runtime: str = "?"
    model: str = "?"
    healthy: bool = True

class AgentUpdate(BaseModel):
    status: Literal["online", "offline", "busy"]

class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    status: Literal["todo", "in_progress", "review", "done"] = "todo"
    priority: Literal["low", "medium", "high"] = "medium"
    assignee_agent_id: Optional[str] = None
    project_id: str = "default"
