from __future__ import annotations

from typing import Any

from mcp import types

from backend.client.session_wrapper import SessionWrapper
from backend.utils.logger import get_logger

logger = get_logger("resource_service")


class ResourceService:
    def __init__(self, session_wrapper: SessionWrapper):
        self._wrapper = session_wrapper

    async def list_resources(self, force_refresh: bool = False) -> list[types.Resource]:
        return await self._wrapper.list_resources(force_refresh)

    async def list_resource_templates(
        self, force_refresh: bool = False
    ) -> list[types.ResourceTemplate]:
        return await self._wrapper.list_resource_templates(force_refresh)

    async def read_resource(self, uri: str) -> types.ReadResourceResult:
        return await self._wrapper.read_resource(uri)

    async def subscribe_resource(self, uri: str) -> None:
        await self._wrapper.subscribe_resource(uri)

    async def unsubscribe_resource(self, uri: str) -> None:
        await self._wrapper.unsubscribe_resource(uri)

    @staticmethod
    def detect_content_type(content: types.TextResourceContents | types.BlobResourceContents) -> str:
        if hasattr(content, "text"):
            text = content.text
            if text.strip().startswith(("<!", "<?xml", "<svg")):
                return "xml"
            if text.strip().startswith("{") or text.strip().startswith("["):
                return "json"
            if text.strip().startswith("#") or text.strip().startswith("<html"):
                return "html"
            return "text"
        if hasattr(content, "blob"):
            mime = getattr(content, "mimeType", "application/octet-stream")
            if mime.startswith("image/"):
                return "image"
            return "binary"
        return "unknown"

    @staticmethod
    def render_resource_content(content: Any) -> dict[str, Any]:
        result: dict[str, Any] = {"type": "unknown", "data": None}

        if hasattr(content, "text"):
            result["type"] = "text"
            result["data"] = content.text
            mime = getattr(content, "mimeType", "")
            if mime:
                result["mime"] = mime
        elif hasattr(content, "blob"):
            import base64

            result["type"] = "blob"
            result["data"] = content.blob
            result["mime"] = getattr(content, "mimeType", "application/octet-stream")
            try:
                result["decoded"] = base64.b64decode(content.blob).decode("utf-8", errors="replace")
            except Exception:
                result["decoded"] = None
        else:
            result["data"] = str(content)

        return result
