from fastapi import APIRouter, HTTPException

from ..services.tool_service import ToolService
from .state import app_state

router = APIRouter()


def _get_tool_service() -> ToolService:
    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")
    return ToolService(wrapper)


@router.get("")
async def list_tools(force_refresh: bool = False):
    svc = _get_tool_service()
    tools = await svc.list_tools(force_refresh=force_refresh)
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema,
            }
            for t in tools
        ]
    }


@router.get("/{name}")
async def get_tool(name: str):
    svc = _get_tool_service()
    tool = await svc.get_tool(name)
    if not tool:
        raise HTTPException(404, f"Tool '{name}' not found")
    return {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": tool.inputSchema,
        "form_fields": ToolService.generate_form_fields(tool.inputSchema),
    }


@router.post("/{name}/call")
async def call_tool(name: str, body: dict):
    svc = _get_tool_service()
    arguments = body.get("arguments")
    result, duration_ms = await svc.call_tool(name, arguments)

    content_list = []
    for c in result.content:
        item = {"type": c.type}
        if hasattr(c, "text"):
            item["text"] = c.text
        if hasattr(c, "data"):
            item["data"] = c.data
        if hasattr(c, "mimeType"):
            item["mimeType"] = c.mimeType
        content_list.append(item)

    return {
        "content": content_list,
        "is_error": result.isError if hasattr(result, "isError") else False,
        "duration_ms": duration_ms,
    }


@router.get("/{name}/history")
async def tool_call_history(name: str):
    svc = _get_tool_service()
    history = svc.get_call_history(name)
    return {
        "history": [
            {
                "tool_name": h.tool_name,
                "arguments": h.arguments,
                "duration_ms": h.duration_ms,
                "timestamp": h.timestamp.isoformat(),
                "is_error": h.is_error,
            }
            for h in history
        ]
    }
