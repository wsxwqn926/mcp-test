import base64

from fastapi import APIRouter, HTTPException, Query

from ..services.resource_service import ResourceService
from .state import app_state

router = APIRouter()


def _get_resource_service(config_id: str | None = None) -> ResourceService:
    if config_id:
        mgr = app_state.get_connection(config_id)
        if not mgr or not mgr.session_wrapper:
            raise HTTPException(400, f"Connection '{config_id}' not active")
        return ResourceService(mgr.session_wrapper)
    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")
    return ResourceService(wrapper)


@router.get("")
async def list_resources(force_refresh: bool = False, config_id: str | None = Query(None)):
    svc = _get_resource_service(config_id)
    try:
        resources = await svc.list_resources(force_refresh=force_refresh)
    except Exception as e:
        if "not found" in str(e).lower() or "not supported" in str(e).lower():
            return {"resources": []}
        raise HTTPException(500, str(e))
    return {
        "resources": [
            {
                "uri": r.uri,
                "name": r.name,
                "description": getattr(r, "description", None),
                "mimeType": getattr(r, "mimeType", None),
            }
            for r in resources
        ]
    }


@router.get("/templates")
async def list_templates(force_refresh: bool = False):
    svc = _get_resource_service()
    try:
        templates = await svc.list_resource_templates(force_refresh=force_refresh)
    except Exception as e:
        if "not found" in str(e).lower() or "not supported" in str(e).lower():
            return {"templates": []}
        raise HTTPException(500, str(e))
    return {
        "templates": [
            {
                "uriTemplate": t.uriTemplate,
                "name": t.name,
                "description": getattr(t, "description", None),
            }
            for t in templates
        ]
    }


@router.post("/read")
async def read_resource(body: dict):
    config_id = body.get("config_id")
    svc = _get_resource_service(config_id)
    uri = body.get("uri")
    if not uri:
        raise HTTPException(400, "uri is required")

    result = await svc.read_resource(uri)

    contents = []
    for c in result.contents:
        item = {"uri": c.uri, "mimeType": getattr(c, "mimeType", None)}
        if hasattr(c, "text"):
            item["text"] = c.text
        if hasattr(c, "blob"):
            blob = c.blob
            if isinstance(blob, bytes):
                item["blob"] = base64.b64encode(blob).decode()
            else:
                item["blob"] = blob
        contents.append(item)

    return {"contents": contents}


@router.post("/subscribe")
async def subscribe_resource(body: dict):
    svc = _get_resource_service()
    uri = body.get("uri")
    if not uri:
        raise HTTPException(400, "uri is required")
    await svc.subscribe_resource(uri)
    return {"subscribed": uri}


@router.post("/unsubscribe")
async def unsubscribe_resource(body: dict):
    svc = _get_resource_service()
    uri = body.get("uri")
    if not uri:
        raise HTTPException(400, "uri is required")
    await svc.unsubscribe_resource(uri)
    return {"unsubscribed": uri}
