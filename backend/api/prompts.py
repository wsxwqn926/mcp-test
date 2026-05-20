from fastapi import APIRouter, HTTPException

from ..services.prompt_service import PromptService
from .state import app_state

router = APIRouter()


def _get_prompt_service() -> PromptService:
    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")
    return PromptService(wrapper)


@router.get("")
async def list_prompts(force_refresh: bool = False):
    svc = _get_prompt_service()
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
    svc = _get_prompt_service()
    arguments = (body or {}).get("arguments")
    result = await svc.get_prompt(name, arguments)
    messages = PromptService.format_prompt_messages(result)
    return {
        "description": getattr(result, "description", None),
        "messages": messages,
    }
