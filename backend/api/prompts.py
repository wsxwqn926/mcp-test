from fastapi import APIRouter, HTTPException, Query

from ..services.prompt_service import PromptService
from .state import app_state

router = APIRouter()


def _get_prompt_service(config_id: str | None = None) -> PromptService:
    if config_id:
        mgr = app_state.get_connection(config_id)
        if not mgr or not mgr.session_wrapper:
            raise HTTPException(400, f"Connection '{config_id}' not active")
        return PromptService(mgr.session_wrapper)
    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")
    return PromptService(wrapper)


@router.get("")
async def list_prompts(force_refresh: bool = False, config_id: str | None = Query(None)):
    svc = _get_prompt_service(config_id)
    try:
        prompts = await svc.list_prompts(force_refresh=force_refresh)
    except Exception as e:
        if "not found" in str(e).lower() or "not supported" in str(e).lower():
            return {"prompts": []}
        raise HTTPException(500, str(e))
    return {
        "prompts": [
            {
                "name": p.name,
                "description": getattr(p, "description", None),
                "arguments": [
                    {
                        "name": a.name,
                        "description": getattr(a, "description", None),
                        "required": getattr(a, "required", False),
                    }
                    for a in (p.arguments or [])
                ]
                if hasattr(p, "arguments") and p.arguments
                else [],
            }
            for p in prompts
        ]
    }


@router.post("/{name}/get")
async def get_prompt(name: str, body: dict = None):
    body = body or {}
    config_id = body.get("config_id")
    svc = _get_prompt_service(config_id)
    arguments = body.get("arguments")
    result = await svc.get_prompt(name, arguments)
    messages = PromptService.format_prompt_messages(result)
    return {
        "description": getattr(result, "description", None),
        "messages": messages,
    }
