from pydantic import BaseModel
from typing import Literal, Optional

class Agent(BaseModel):
    id: str
    name: str
    status: Literal["online", "offline", "busy"] = "online"
    runtime: str = "?"
    model: str = "?"
    healthy: bool = True
    cpu: float = 0
    active_runs: int = 0
    tokens_used: int = 0
    tokens_limit: int = 100000
    budget_used: float = 0
    budget_limit: float = 50
    account: str = ""
    provider: str = ""

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
