from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TransportType(str, Enum):
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


class StdioConfig(BaseModel):
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    cwd: str | None = None


class HttpConfig(BaseModel):
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: float = 30.0


class ServerConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    transport_type: TransportType
    stdio_config: StdioConfig | None = None
    http_config: HttpConfig | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def to_display_string(self) -> str:
        if self.transport_type == TransportType.STDIO and self.stdio_config:
            parts = [self.stdio_config.command] + self.stdio_config.args
            return f"{self.name} ({' '.join(parts)})"
        if self.transport_type == TransportType.HTTP and self.http_config:
            return f"{self.name} ({self.http_config.url})"
        return self.name


class ToolCapabilities(BaseModel):
    list_changed: bool = False


class ResourceCapabilities(BaseModel):
    subscribe: bool = False
    list_changed: bool = False


class PromptCapabilities(BaseModel):
    list_changed: bool = False


class LoggingCapabilities(BaseModel):
    pass


class ServerCapabilities(BaseModel):
    tools: ToolCapabilities | None = None
    resources: ResourceCapabilities | None = None
    prompts: PromptCapabilities | None = None
    logging: LoggingCapabilities | None = None


class ServerInfo(BaseModel):
    name: str
    version: str
    protocol_version: str
    capabilities: ServerCapabilities = Field(default_factory=ServerCapabilities)


class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    INITIALIZING = "initializing"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"


class ConnectionSession(BaseModel):
    config_id: str
    state: ConnectionState = ConnectionState.DISCONNECTED
    server_info: ServerInfo | None = None
    connected_at: datetime | None = None
    error_message: str | None = None
