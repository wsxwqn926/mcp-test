from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    START = "start"
    END = "end"
    TOOL_CALL = "tool_call"
    RESOURCE_READ = "resource_read"
    PROMPT_GET = "prompt_get"
    ASSERTION = "assertion"
    WAIT = "wait"
    CONDITION = "condition"
    VARIABLE = "variable"
    LOOP = "loop"


class WorkflowNode(BaseModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    type: NodeType
    position: dict = {"x": 0, "y": 0}
    label: str | None = None
    data: dict = {}


class WorkflowEdge(BaseModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    source: str
    target: str
    source_handle: str | None = None
    label: str | None = None
    data: dict | None = None


class Workflow(BaseModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    name: str
    description: str | None = None
    nodes: list[WorkflowNode] = []
    edges: list[WorkflowEdge] = []
    variables: dict[str, Any] = {}
    tags: list[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
