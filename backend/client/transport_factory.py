from __future__ import annotations

import httpx
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client

from backend.models.server_config import HttpConfig, ServerConfig, StdioConfig, TransportType


def create_stdio_params(config: StdioConfig) -> StdioServerParameters:
    return StdioServerParameters(
        command=config.command,
        args=config.args,
        env=config.env,
        cwd=config.cwd,
    )


def get_transport_context(config: ServerConfig):
    if config.transport_type == TransportType.STDIO:
        if config.stdio_config is None:
            raise ValueError("STDIO 配置不能为空")
        return stdio_client(create_stdio_params(config.stdio_config))

    if config.transport_type == TransportType.HTTP:
        if config.http_config is None:
            raise ValueError("HTTP 配置不能为空")
        kwargs: dict = {"url": config.http_config.url}
        if config.http_config.headers:
            kwargs["http_client"] = httpx.AsyncClient(
                headers=config.http_config.headers,
                timeout=httpx.Timeout(config.http_config.timeout),
            )
        return streamable_http_client(**kwargs)

    if config.transport_type == TransportType.SSE:
        if config.http_config is None:
            raise ValueError("SSE 配置不能为空")
        return sse_client(
            url=config.http_config.url,
            headers=config.http_config.headers or None,
        )

        raise ValueError(f"不支持的传输类型: {config.transport_type}")
