from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class MessageLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    direction: Literal["request", "response", "notification"]
    timestamp: datetime = Field(default_factory=datetime.now)
    method: str | None = None
    request_id: int | str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float | None = None
    error: dict[str, Any] | None = None

    def is_request(self) -> bool:
        return self.direction == "request"

    def is_response(self) -> bool:
        return self.direction == "response"

    def is_notification(self) -> bool:
        return self.direction == "notification"

    def is_error_response(self) -> bool:
        return self.direction == "response" and self.error is not None

    def get_summary(self) -> str:
        dir_symbol = {"request": "→", "response": "←", "notification": "↔"}[self.direction]
        method_str = self.method or "unknown"
        parts = [f"{dir_symbol} {self.timestamp.strftime('%H:%M:%S.%f')[:-3]}"]
        parts.append(method_str)
        if self.request_id is not None:
            parts.append(f"id:{self.request_id}")
        if self.duration_ms is not None:
            parts.append(f"{self.duration_ms:.0f}ms")
        if self.is_error_response():
            parts.append("ERROR")
        return " ".join(parts)


class MessageFilter(BaseModel):
    session_id: str | None = None
    direction: Literal["request", "response", "notification"] | None = None
    method: str | None = None
    search_text: str | None = None
    limit: int = 500
