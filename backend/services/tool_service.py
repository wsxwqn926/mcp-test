from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mcp import types

from backend.client.session_wrapper import SessionWrapper
from backend.utils.logger import get_logger

logger = get_logger("tool_service")


@dataclass
class ToolCallRecord:
    tool_name: str
    arguments: dict[str, Any] | None
    result: types.CallToolResult
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    is_error: bool = False


class ToolService:
    def __init__(self, session_wrapper: SessionWrapper):
        self._wrapper = session_wrapper
        self._call_history: dict[str, deque[ToolCallRecord]] = {}
        self._history_lock = threading.Lock()
        self._max_history_per_tool = 50

    async def list_tools(self, force_refresh: bool = False) -> list[types.Tool]:
        return await self._wrapper.list_tools(force_refresh)

    async def get_tool(self, name: str) -> types.Tool | None:
        tools = await self.list_tools()
        for t in tools:
            if t.name == name:
                return t
        return None

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> tuple[types.CallToolResult, float]:
        import time

        start = time.monotonic()
        result = await self._wrapper.call_tool(name, arguments)
        duration = (time.monotonic() - start) * 1000

        record = ToolCallRecord(
            tool_name=name,
            arguments=arguments,
            result=result,
            duration_ms=duration,
            is_error=result.isError or False,
        )
        with self._history_lock:
            if name not in self._call_history:
                self._call_history[name] = deque(maxlen=self._max_history_per_tool)
            self._call_history[name].append(record)

        return result, duration

    def get_call_history(self, tool_name: str | None = None) -> list[ToolCallRecord]:
        with self._history_lock:
            if tool_name:
                return list(self._call_history.get(tool_name, []))
            all_records: list[ToolCallRecord] = []
            for records in self._call_history.values():
                all_records.extend(records)
            all_records.sort(key=lambda r: r.timestamp, reverse=True)
            return all_records

    @staticmethod
    def generate_form_fields(
        schema: dict[str, Any],
    ) -> list[dict[str, Any]]:
        fields = []
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "string")
            field_info: dict[str, Any] = {
                "name": prop_name,
                "type": prop_type,
                "required": prop_name in required,
                "description": prop_def.get("description", ""),
                "default": prop_def.get("default"),
            }

            if prop_type == "string" and "enum" in prop_def:
                field_info["widget"] = "selectbox"
                field_info["options"] = prop_def["enum"]
            elif prop_type == "string":
                field_info["widget"] = "text_input"
            elif prop_type in ("number", "integer"):
                field_info["widget"] = "number_input"
                field_info["min_value"] = prop_def.get("minimum")
                field_info["max_value"] = prop_def.get("maximum")
            elif prop_type == "boolean":
                field_info["widget"] = "checkbox"
            else:
                field_info["widget"] = "text_input"

            fields.append(field_info)

        return fields
