from fastapi import APIRouter, HTTPException, Query

from ..services.tool_service import ToolService
from .state import app_state

router = APIRouter()


def _get_tool_service(config_id: str | None = None) -> ToolService:
    if config_id:
        mgr = app_state.get_connection(config_id)
        if not mgr or not mgr.session_wrapper:
            raise HTTPException(400, f"Connection '{config_id}' not active")
        return ToolService(mgr.session_wrapper)
    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")
    return ToolService(wrapper)


@router.get("")
async def list_tools(force_refresh: bool = False, config_id: str | None = Query(None)):
    svc = _get_tool_service(config_id)
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


@router.get("/all")
async def list_all_tools(force_refresh: bool = False):
    result = {}
    for cid, mgr in app_state.list_connections().items():
        if mgr.session_wrapper:
            try:
                svc = ToolService(mgr.session_wrapper)
                tools = await svc.list_tools(force_refresh=force_refresh)
                result[cid] = {
                    "tools": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "inputSchema": t.inputSchema,
                        }
                        for t in tools
                    ]
                }
            except Exception as e:
                result[cid] = {"tools": [], "error": str(e)}
    return result


@router.get("/{name}")
async def get_tool(name: str, config_id: str | None = Query(None)):
    svc = _get_tool_service(config_id)
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
    config_id = body.get("config_id")
    svc = _get_tool_service(config_id)
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
