from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssertionType(str, Enum):
    STATUS_SUCCESS = "status_success"
    CONTENT_CONTAINS = "content_contains"
    CONTENT_MATCHES = "content_matches"
    CONTENT_SCHEMA_VALID = "content_schema_valid"
    RESPONSE_TIME_LT = "response_time_lt"
    CONTENT_NOT_EMPTY = "content_not_empty"
    JSON_FIELD_EQUALS = "json_field_equals"


class Assertion(BaseModel):
    type: AssertionType
    expected: Any = None
    path: str | None = None
    negate: bool = False


class StepType(str, Enum):
    TOOL_CALL = "tool_call"
    RESOURCE_READ = "resource_read"
    PROMPT_GET = "prompt_get"
    ASSERTION = "assertion"
    WAIT = "wait"


class TestStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: StepType
    name: str | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None
    resource_uri: str | None = None
    prompt_name: str | None = None
    prompt_arguments: dict[str, str] | None = None
    assertion: Assertion | None = None
    wait_seconds: float | None = None


class TestCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str | None = None
    server_config_id: str | None = None
    steps: list[TestStep] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
