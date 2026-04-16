from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "node_start",
    "node_end",
    "llm_chunk",
    "tool_call",
    "error",
]


class AgentEvent(BaseModel):
    ts: datetime = Field(default_factory=datetime.utcnow)
    node: str
    type: EventType
    payload: dict[str, Any] = {}
