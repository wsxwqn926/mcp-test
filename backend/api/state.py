import asyncio
import json
from fastapi import WebSocket

from ..client.connection_manager import ConnectionManager
from ..models.message_log import MessageLog
from ..models.server_config import ConnectionState, ServerConfig
from ..services.message_logger import MessageLogger


class AppState:
    def __init__(self):
        self.connection_manager: ConnectionManager | None = None
        self.message_logger = MessageLogger()
        self.current_config: ServerConfig | None = None
        self._ws_connections: list[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None
        self._secondary: dict[str, ConnectionManager] = {}

    def add_secondary(self, config_id: str, mgr: ConnectionManager):
        self._secondary[config_id] = mgr

    def remove_secondary(self, config_id: str):
        mgr = self._secondary.pop(config_id, None)
        if mgr and mgr.is_connected() and self._loop:
            asyncio.run_coroutine_threadsafe(mgr.disconnect(), self._loop)

    def get_secondary(self, config_id: str) -> ConnectionManager | None:
        return self._secondary.get(config_id)

    def list_secondary(self) -> list[str]:
        return list(self._secondary.keys())

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def add_ws(self, ws: WebSocket):
        self._ws_connections.append(ws)

    def remove_ws(self, ws: WebSocket):
        if ws in self._ws_connections:
            self._ws_connections.remove(ws)

    async def broadcast(self, event_type: str, data: dict):
        msg = json.dumps({"type": event_type, "data": data}, ensure_ascii=False, default=str)
        disconnected = []
        for i, ws in enumerate(self._ws_connections):
            try:
                await ws.send_text(msg)
            except Exception:
                disconnected.append(i)
        for i in reversed(disconnected):
            self._ws_connections.pop(i)

    def emit(self, event_type: str, data: dict):
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.broadcast(event_type, data), self._loop
            )

    def on_message(self, msg: MessageLog):
        self.message_logger.add(msg)
        self.emit("message_log", msg.model_dump(mode="json"))
        if msg.is_notification():
            self.emit("server_notification", msg.model_dump(mode="json"))

    def on_state_change(self, state: ConnectionState):
        if state == ConnectionState.DISCONNECTED and self.message_logger.count > 0:
            try:
                self.message_logger.save_to_file()
            except Exception:
                pass
        data: dict = {"state": state.value}
        if self.connection_manager:
            session = self.connection_manager.connection_session
            if session and session.server_info:
                data["server_info"] = session.server_info.model_dump(mode="json")
        self.emit("connection_state", data)

    @property
    def is_connected(self) -> bool:
        return self.connection_manager is not None and self.connection_manager.is_connected()

    def get_session_wrapper(self):
        if self.connection_manager and self.connection_manager.session_wrapper:
            return self.connection_manager.session_wrapper
        return None


app_state = AppState()
