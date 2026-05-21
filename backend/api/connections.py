import traceback

from fastapi import APIRouter, HTTPException

from ..client.connection_manager import ConnectionManager
from ..models.server_config import ServerConfig, ServerInfo, StdioConfig, HttpConfig, TransportType
from ..utils.config import load_server_configs, save_server_config, delete_server_config as delete_config
from .state import app_state

router = APIRouter()


def _friendly_error(e: Exception) -> str:
    err_msg = str(e)
    traceback.print_exc()
    if "Connection closed" in err_msg:
        return "连接被关闭，请检查服务器配置和命令是否正确"
    if "timeout" in err_msg.lower():
        return "连接超时，请检查服务器是否可达"
    if "not found" in err_msg.lower():
        return "找不到命令或程序，请检查路径"
    return f"Connection failed: {err_msg}"


@router.get("")
async def list_connections():
    configs = load_server_configs()
    return {"configs": {k: v.model_dump(mode="json") for k, v in configs.items()}}


@router.post("")
async def create_connection(body: dict):
    config = _build_config(body)
    save_server_config(config)
    return config.model_dump(mode="json")


@router.get("/status")
async def connection_status():
    primary_id = app_state.primary_id
    mgr = app_state.connection_manager
    result = {
        "state": mgr.state.value if mgr else "disconnected",
        "config": app_state.current_config.model_dump(mode="json") if app_state.current_config else None,
        "server_info": mgr.get_server_info().model_dump(mode="json") if mgr and mgr.get_server_info() else None,
        "primary_id": primary_id,
        "connections": [],
    }
    for cid, m in app_state.list_connections().items():
        info = {
            "id": cid,
            "name": "",
            "state": m.state.value,
            "server_info": m.get_server_info().model_dump(mode="json") if m.get_server_info() else None,
        }
        if cid == primary_id and app_state.current_config:
            info["name"] = app_state.current_config.name
        else:
            from ..utils.config import load_server_configs
            configs = load_server_configs()
            if cid in configs:
                info["name"] = configs[cid].name
        result["connections"].append(info)
    return result


@router.post("/disconnect")
async def disconnect():
    if not app_state.is_connected:
        return {"disconnected": True}
    try:
        await app_state.connection_manager.disconnect()
    except Exception as e:
        raise HTTPException(500, f"Disconnect failed: {e}")
    finally:
        pid = app_state.primary_id
        if pid:
            app_state.remove_connection(pid)
    return {"disconnected": True}


@router.post("/{config_id}/connect")
async def connect(config_id: str, body: dict | None = None):
    body = body or {}
    configs = load_server_configs()
    if config_id not in configs:
        raise HTTPException(404, "Connection not found")

    existing = app_state.get_connection(config_id)
    if existing and existing.is_connected():
        return {
            "connected": True,
            "server_info": existing.get_server_info().model_dump(mode="json") if existing.get_server_info() else None,
        }

    config = configs[config_id]
    set_primary = body.get("set_primary", True)
    mgr = ConnectionManager(
        on_state_change=app_state.on_state_change,
        on_message=app_state.on_message,
    )

    try:
        await mgr.connect(config)
    except Exception as e:
        raise HTTPException(500, _friendly_error(e))

    app_state.add_connection(config_id, mgr, set_primary=set_primary)
    if set_primary:
        app_state.current_config = config

    return {
        "connected": True,
        "server_info": mgr.get_server_info().model_dump(mode="json") if mgr.get_server_info() else None,
    }


@router.post("/{config_id}/disconnect-connection")
async def disconnect_one(config_id: str):
    mgr = app_state.get_connection(config_id)
    if not mgr:
        return {"disconnected": True}
    try:
        await mgr.disconnect()
    except Exception:
        pass
    app_state.remove_connection(config_id)
    return {"disconnected": True}


@router.put("/primary/{config_id}")
async def set_primary(config_id: str):
    mgr = app_state.get_connection(config_id)
    if not mgr or not mgr.is_connected():
        raise HTTPException(400, "Connection not active")
    app_state.set_primary(config_id)
    return {"primary_id": config_id}


@router.get("/compare")
async def compare_connections():
    result = {}
    for cid, mgr in app_state.list_connections().items():
        info = {}
        if mgr.session_wrapper:
            try:
                tools = await mgr.session_wrapper.list_tools()
                info = {"tools": [{"name": t.name, "description": t.description} for t in tools]}
            except Exception:
                info = {"tools": [], "error": "Failed to list tools"}
        is_primary = cid == app_state.primary_id
        result[cid] = {"config_id": cid, "primary": is_primary, **info}
    return result


@router.get("/{config_id}")
async def get_connection(config_id: str):
    configs = load_server_configs()
    if config_id not in configs:
        raise HTTPException(404, "Connection not found")
    return configs[config_id].model_dump(mode="json")


@router.put("/{config_id}")
async def update_connection(config_id: str, body: dict):
    configs = load_server_configs()
    if config_id not in configs:
        raise HTTPException(404, "Connection not found")
    config = _build_config(body, config_id)
    save_server_config(config)
    return config.model_dump(mode="json")


@router.delete("/{config_id}")
async def delete_connection(config_id: str):
    configs = load_server_configs()
    if config_id not in configs:
        raise HTTPException(404, "Connection not found")
    if app_state.get_connection(config_id):
        app_state.remove_connection(config_id)
    delete_config(config_id)
    return {"deleted": True}


def _build_config(body: dict, config_id: str | None = None) -> ServerConfig:
    from datetime import datetime
    import uuid

    transport_type = TransportType(body.get("transport_type", "stdio"))

    stdio_config = None
    http_config = None

    if transport_type in (TransportType.STDIO,):
        sc = body.get("stdio_config", {})
        stdio_config = StdioConfig(
            command=sc.get("command", ""),
            args=sc.get("args", []),
            env=sc.get("env"),
            cwd=sc.get("cwd"),
        )
    elif transport_type in (TransportType.HTTP, TransportType.SSE):
        hc = body.get("http_config", {})
        http_config = HttpConfig(
            url=hc.get("url", ""),
            headers=hc.get("headers", {}),
            timeout=hc.get("timeout", 30.0),
        )

    now = datetime.now()
    return ServerConfig(
        id=config_id or body.get("id", str(uuid.uuid4())),
        name=body.get("name", "Unnamed"),
        transport_type=transport_type,
        stdio_config=stdio_config,
        http_config=http_config,
        created_at=body.get("created_at", now),
        updated_at=now,
    )
