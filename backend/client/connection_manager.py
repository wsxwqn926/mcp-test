from __future__ import annotations

from datetime import datetime
from typing import Callable

from mcp.client.session import ClientSession

from backend.client.session_wrapper import SessionWrapper
from backend.client.transport_factory import get_transport_context
from backend.models.message_log import MessageLog
from backend.models.server_config import (
    ConnectionState,
    ConnectionSession,
    ServerCapabilities,
    ServerConfig,
    ServerInfo,
    ToolCapabilities,
    ResourceCapabilities,
    PromptCapabilities,
    LoggingCapabilities,
)
from backend.utils.logger import get_logger

logger = get_logger("connection_manager")


class ConnectionManager:
    def __init__(
        self,
        on_state_change: Callable[[ConnectionState], None] | None = None,
        on_message: Callable[[MessageLog], None] | None = None,
    ):
        self._session_wrapper: SessionWrapper | None = None
        self._connection_session: ConnectionSession | None = None
        self._on_state_change = on_state_change
        self._on_message = on_message

    @property
    def session_wrapper(self) -> SessionWrapper | None:
        return self._session_wrapper

    @property
    def connection_session(self) -> ConnectionSession | None:
        return self._connection_session

    @property
    def state(self) -> ConnectionState:
        if self._connection_session is None:
            return ConnectionState.DISCONNECTED
        return self._connection_session.state

    def _set_state(self, new_state: ConnectionState, error: str | None = None) -> None:
        if self._connection_session:
            self._connection_session.state = new_state
            if error:
                self._connection_session.error_message = error
        if self._on_state_change:
            self._on_state_change(new_state)

    def _parse_server_info(self, init_result) -> ServerInfo:
        caps = init_result.capabilities
        server_caps = ServerCapabilities()
        if caps:
            if caps.tools:
                server_caps.tools = ToolCapabilities(
                    list_changed=caps.tools.listChanged or False,
                )
            if caps.resources:
                server_caps.resources = ResourceCapabilities(
                    subscribe=getattr(caps.resources, "subscribe", False) or False,
                    list_changed=caps.resources.listChanged or False,
                )
            if caps.prompts:
                server_caps.prompts = PromptCapabilities(
                    list_changed=caps.prompts.listChanged or False,
                )
            if caps.logging:
                server_caps.logging = LoggingCapabilities()

        return ServerInfo(
            name=init_result.serverInfo.name if init_result.serverInfo else "unknown",
            version=init_result.serverInfo.version if init_result.serverInfo else "0.0.0",
            protocol_version=str(init_result.protocolVersion),
            capabilities=server_caps,
        )

    async def connect(self, config: ServerConfig) -> ConnectionSession:
        if self._session_wrapper and self._session_wrapper.is_connected:
            await self.disconnect()

        self._connection_session = ConnectionSession(config_id=config.id)
        self._set_state(ConnectionState.CONNECTING)

        try:
            self._session_wrapper = SessionWrapper(on_message=self._on_message)
            transport_ctx = get_transport_context(config)

            from contextlib import AsyncExitStack

            exit_stack = AsyncExitStack()
            transport_result = await exit_stack.enter_async_context(
                transport_ctx
            )
            if isinstance(transport_result, tuple):
                if len(transport_result) == 3:
                    read_stream, write_stream, _session_info = transport_result
                else:
                    read_stream, write_stream = transport_result
            else:
                raise ValueError(f"Unexpected transport result type: {type(transport_result)}")

            client_session = await exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            self._session_wrapper.set_session(client_session, exit_stack)
            self._set_state(ConnectionState.INITIALIZING)

            init_result = await self._session_wrapper.initialize()

            server_info = self._parse_server_info(init_result)
            self._connection_session.server_info = server_info
            self._connection_session.connected_at = datetime.now()
            self._set_state(ConnectionState.CONNECTED)

            logger.info(
                f"Connected to {server_info.name} v{server_info.version} "
                f"(protocol: {server_info.protocol_version})"
            )
            return self._connection_session

        except Exception as e:
            error_msg = f"Connection error: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._set_state(ConnectionState.ERROR, error_msg)
            if self._session_wrapper:
                try:
                    await self._session_wrapper.close()
                except Exception:
                    pass
                self._session_wrapper = None
            raise

    async def disconnect(self) -> None:
        if not self._session_wrapper:
            return

        self._set_state(ConnectionState.DISCONNECTING)
        try:
            await self._session_wrapper.close()
        except Exception as e:
            logger.warning(f"Disconnect warning? {e}")
        finally:
            self._session_wrapper = None
            if self._connection_session:
                self._connection_session.connected_at = None
            self._set_state(ConnectionState.DISCONNECTED)
            logger.info("Disconnected")

    async def reconnect(self, config: ServerConfig) -> ConnectionSession:
        await self.disconnect()
        return await self.connect(config)

    def get_server_info(self) -> ServerInfo | None:
        if self._connection_session:
            return self._connection_session.server_info
        return None

    def is_connected(self) -> bool:
        return (
            self.state == ConnectionState.CONNECTED
            and self._session_wrapper is not None
            and self._session_wrapper.is_connected
        )
