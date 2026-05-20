from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssertionResult(BaseModel):
    assertion_type: str
    passed: bool
    expected: Any = None
    actual: Any = None
    message: str = ""


class StepResult(BaseModel):
    step_id: str
    step_name: str | None = None
    step_type: str
    status: Literal["passed", "failed", "error", "skipped"] = "passed"
    duration_ms: float = 0.0
    request: dict[str, Any] | None = None
    response: dict[str, Any] | None = None
    assertion_results: list[AssertionResult] = Field(default_factory=list)
    error_message: str | None = None


class TestRunResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_case_id: str
    test_case_name: str = ""
    status: Literal["passed", "failed", "error", "skipped"] = "passed"
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = None
    duration_ms: float = 0.0
    step_results: list[StepResult] = Field(default_factory=list)
    total_steps: int = 0
    passed_steps: int = 0
    failed_steps: int = 0
    error_message: str | None = None
