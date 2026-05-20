from __future__ import annotations

import time
import uuid
import threading
from contextlib import AsyncExitStack
from collections import deque
from datetime import datetime
from typing import Any, Callable

from mcp import types
from mcp.client.session import ClientSession

from backend.models.message_log import MessageLog
from backend.utils.logger import get_logger

logger = get_logger("session_wrapper")


class SessionWrapper:
    def __init__(
        self,
        on_message: Callable[[MessageLog], None] | None = None,
    ):
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self._session_id: str = str(uuid.uuid4())
        self._on_message = on_message
        self._message_buffer: deque[MessageLog] = deque(maxlen=1000)
        self._buffer_lock = threading.Lock()
        self._tool_cache: list[types.Tool] | None = None
        self._resource_cache: list[types.Resource] | None = None
        self._resource_template_cache: list[types.ResourceTemplate] | None = None
        self._prompt_cache: list[types.Prompt] | None = None
        self._initialize_result: types.InitializeResult | None = None

    def drain_message_buffer(self) -> list[MessageLog]:
        with self._buffer_lock:
            msgs = list(self._message_buffer)
            self._message_buffer.clear()
            return msgs

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def session(self) -> ClientSession | None:
        return self._session

    @property
    def is_connected(self) -> bool:
        return self._session is not None

    @property
    def initialize_result(self) -> types.InitializeResult | None:
        return self._initialize_result

    def set_session(self, session: ClientSession, exit_stack: AsyncExitStack) -> None:
        self._session = session
        self._exit_stack = exit_stack
        try:
            session._notification_handler = self._on_notification
        except Exception:
            pass

    def _on_notification(self, notification: Any) -> None:
        method = getattr(notification, "method", None) or getattr(notification, "root", None)
        if isinstance(method, object) and hasattr(method, "method"):
            method = method.method
        method_str = str(method) if method else "notification"
        data = {}
        try:
            data = notification.model_dump(mode="json") if hasattr(notification, "model_dump") else str(notification)
        except Exception:
            data = {"raw": str(notification)}
        log = MessageLog(
            session_id=self._session_id,
            direction="notification",
            method=method_str,
            data=data,
        )
        with self._buffer_lock:
            self._message_buffer.append(log)
        if self._on_message:
            self._on_message(log)

    def invalidate_caches(self) -> None:
        self._tool_cache = None
        self._resource_cache = None
        self._resource_template_cache = None
        self._prompt_cache = None

    def _log_request(self, method: str, data: dict[str, Any]) -> None:
        log = MessageLog(
            session_id=self._session_id,
            direction="request",
            method=method,
            request_id=data.get("id"),
            data=data,
        )
        with self._buffer_lock:
            self._message_buffer.append(log)
        if self._on_message:
            self._on_message(log)

    def _log_response(
        self,
        method: str,
        data: dict[str, Any],
        duration_ms: float,
        request_id: int | str | None = None,
    ) -> None:
        error = data.get("error")
        log = MessageLog(
            session_id=self._session_id,
            direction="response",
            method=method,
            request_id=request_id,
            data=data,
            duration_ms=duration_ms,
            error=error,
        )
        with self._buffer_lock:
            self._message_buffer.append(log)
        if self._on_message:
            self._on_message(log)

    async def initialize(self) -> types.InitializeResult:
        if not self._session:
            raise RuntimeError("会话未建立")
        start = time.monotonic()
        result = await self._session.initialize()
        duration = (time.monotonic() - start) * 1000
        self._initialize_result = result
        self._log_response("initialize", result.model_dump(mode="json"), duration)
        return result

    async def list_tools(self, force_refresh: bool = False) -> list[types.Tool]:
        if not self._session:
            raise RuntimeError("会话未建立")
        if self._tool_cache is not None and not force_refresh:
            return self._tool_cache
        start = time.monotonic()
        result = await self._session.list_tools()
        duration = (time.monotonic() - start) * 1000
        self._log_response("tools/list", result.model_dump(mode="json"), duration)
        self._tool_cache = result.tools
        return result.tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> types.CallToolResult:
        if not self._session:
            raise RuntimeError("会话未建立")
        self._log_request("tools/call", {"name": name, "arguments": arguments})
        start = time.monotonic()
        result = await self._session.call_tool(name, arguments)
        duration = (time.monotonic() - start) * 1000
        self._log_response(
            "tools/call",
            result.model_dump(mode="json"),
            duration,
        )
        return result

    async def list_resources(self, force_refresh: bool = False) -> list[types.Resource]:
        if not self._session:
            raise RuntimeError("会话未建立")
        if self._resource_cache is not None and not force_refresh:
            return self._resource_cache
        start = time.monotonic()
        result = await self._session.list_resources()
        duration = (time.monotonic() - start) * 1000
        self._log_response("resources/list", result.model_dump(mode="json"), duration)
        self._resource_cache = result.resources
        return result.resources

    async def list_resource_templates(
        self, force_refresh: bool = False
    ) -> list[types.ResourceTemplate]:
        if not self._session:
            raise RuntimeError("会话未建立")
        if self._resource_template_cache is not None and not force_refresh:
            return self._resource_template_cache
        start = time.monotonic()
        result = await self._session.list_resource_templates()
        duration = (time.monotonic() - start) * 1000
        self._log_response(
            "resources/templates/list", result.model_dump(mode="json"), duration
        )
        self._resource_template_cache = result.resource_templates
        return result.resource_templates

    async def read_resource(self, uri: str) -> types.ReadResourceResult:
        if not self._session:
            raise RuntimeError("会话未建立")
        self._log_request("resources/read", {"uri": uri})
        start = time.monotonic()
        result = await self._session.read_resource(uri)
        duration = (time.monotonic() - start) * 1000
        self._log_response("resources/read", result.model_dump(mode="json"), duration)
        return result

    async def subscribe_resource(self, uri: str) -> None:
        if not self._session:
            raise RuntimeError("会话未建立")
        await self._session.subscribe_resource(uri)

    async def unsubscribe_resource(self, uri: str) -> None:
        if not self._session:
            raise RuntimeError("会话未建立")
        await self._session.unsubscribe_resource(uri)

    async def list_prompts(self, force_refresh: bool = False) -> list[types.Prompt]:
        if not self._session:
            raise RuntimeError("会话未建立")
        if self._prompt_cache is not None and not force_refresh:
            return self._prompt_cache
        start = time.monotonic()
        result = await self._session.list_prompts()
        duration = (time.monotonic() - start) * 1000
        self._log_response("prompts/list", result.model_dump(mode="json"), duration)
        self._prompt_cache = result.prompts
        return result.prompts

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None,
    ) -> types.GetPromptResult:
        if not self._session:
            raise RuntimeError("会话未建立")
        self._log_request("prompts/get", {"name": name, "arguments": arguments})
        start = time.monotonic()
        result = await self._session.get_prompt(name, arguments)
        duration = (time.monotonic() - start) * 1000
        self._log_response("prompts/get", result.model_dump(mode="json"), duration)
        return result

    async def send_ping(self) -> types.EmptyResult:
        if not self._session:
            raise RuntimeError("会话未建立")
        return await self._session.send_ping()

    async def close(self) -> None:
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
        self._session = None
        self._initialize_result = None
        self.invalidate_caches()
