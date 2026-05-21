from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .test_result import AssertionResult


class NodeResult(BaseModel):
    node_id: str
    node_type: str
    node_label: str | None = None
    status: str = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: float = 0
    request: dict | None = None
    response: dict | None = None
    error_message: str | None = None
    assertion_results: list[AssertionResult] = []


class WorkflowRunResult(BaseModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    workflow_id: str
    workflow_name: str
    status: str = "running"
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = None
    duration_ms: float = 0
    node_results: dict[str, NodeResult] = {}
    variables_snapshot: dict[str, Any] = {}
    error_message: str | None = None
