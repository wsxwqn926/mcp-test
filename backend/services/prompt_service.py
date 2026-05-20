from __future__ import annotations

from typing import Any

from mcp import types

from backend.client.session_wrapper import SessionWrapper
from backend.utils.logger import get_logger

logger = get_logger("prompt_service")


class PromptService:
    def __init__(self, session_wrapper: SessionWrapper):
        self._wrapper = session_wrapper

    async def list_prompts(self, force_refresh: bool = False) -> list[types.Prompt]:
        return await self._wrapper.list_prompts(force_refresh)

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None,
    ) -> types.GetPromptResult:
        return await self._wrapper.get_prompt(name, arguments)

    @staticmethod
    def generate_form_fields(prompt: types.Prompt) -> list[dict[str, Any]]:
        fields = []
        arguments = getattr(prompt, "arguments", None) or []
        for arg in arguments:
            field_info: dict[str, Any] = {
                "name": arg.name,
                "required": getattr(arg, "required", False),
                "description": getattr(arg, "description", ""),
                "widget": "text_input",
            }
            fields.append(field_info)
        return fields

    @staticmethod
    def format_prompt_messages(
        result: types.GetPromptResult,
    ) -> list[dict[str, Any]]:
        messages = []
        for msg in result.messages:
            role = msg.role if hasattr(msg, "role") else "unknown"
            content = msg.content if hasattr(msg, "content") else msg

            formatted: dict[str, Any] = {"role": role}

            if hasattr(content, "text"):
                formatted["type"] = "text"
                formatted["content"] = content.text
            elif hasattr(content, "data"):
                formatted["type"] = "image"
                formatted["content"] = content.data
                formatted["mime"] = getattr(content, "mimeType", "")
            else:
                formatted["type"] = "unknown"
                formatted["content"] = str(content)

            messages.append(formatted)

        return messages
