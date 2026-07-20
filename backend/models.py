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
