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
    mgr = app_state.connection_manager
    return {
        "state": mgr.state.value if mgr else "disconnected",
        "config": app_state.current_config.model_dump(mode="json") if app_state.current_config else None,
        "server_info": mgr.get_server_info().model_dump(mode="json") if mgr and mgr.get_server_info() else None,
    }


@router.post("/disconnect")
async def disconnect():
    if not app_state.is_connected:
        return {"disconnected": True}
    try:
        await app_state.connection_manager.disconnect()
    except Exception as e:
        raise HTTPException(500, f"Disconnect failed: {e}")
    finally:
        app_state.connection_manager = None
        app_state.current_config = None
    return {"disconnected": True}


@router.post("/{config_id}/connect")
async def connect(config_id: str):
    configs = load_server_configs()
    if config_id not in configs:
        raise HTTPException(404, "Connection not found")

    if app_state.is_connected:
        await app_state.connection_manager.disconnect()

    config = configs[config_id]
    mgr = ConnectionManager(
        on_state_change=app_state.on_state_change,
        on_message=app_state.on_message,
    )

    try:
        await mgr.connect(config)
    except Exception as e:
        raise HTTPException(500, _friendly_error(e))

    app_state.connection_manager = mgr
    app_state.current_config = config

    return {
        "connected": True,
        "server_info": mgr.get_server_info().model_dump(mode="json") if mgr.get_server_info() else None,
    }


@router.get("/compare")
async def compare_connections():
    result = {}
    primary = {}
    if app_state.is_connected and app_state.connection_manager:
        wrapper = app_state.connection_manager.session_wrapper
        if wrapper:
            try:
                tools = await wrapper.list_tools()
                primary = {"tools": [{"name": t.name, "description": t.description} for t in tools]}
            except Exception:
                primary = {"tools": [], "error": "Failed to list tools"}
    result["primary"] = {"config_id": app_state.current_config.id if app_state.current_config else None, **primary}

    for cid, mgr in app_state._secondary.items():
        info = {}
        if mgr.session_wrapper:
            try:
                tools = await mgr.session_wrapper.list_tools()
                info = {"tools": [{"name": t.name, "description": t.description} for t in tools]}
            except Exception:
                info = {"tools": [], "error": "Failed to list tools"}
        result[cid] = {"config_id": cid, **info}
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
    if app_state.is_connected and app_state.current_config and app_state.current_config.id == config_id:
        await app_state.connection_manager.disconnect()
        app_state.current_config = None
    delete_config(config_id)
    return {"deleted": True}


@router.post("/{config_id}/connect-secondary")
async def connect_secondary(config_id: str):
    configs = load_server_configs()
    if config_id not in configs:
        raise HTTPException(404, "Connection not found")
    if config_id in app_state.list_secondary():
        raise HTTPException(400, "Already connected as secondary")
    config = configs[config_id]
    mgr = ConnectionManager()
    try:
        await mgr.connect(config)
    except Exception as e:
        raise HTTPException(500, _friendly_error(e))
    app_state.add_secondary(config_id, mgr)
    return {"connected": True, "server_info": mgr.get_server_info().model_dump(mode="json") if mgr.get_server_info() else None}


@router.post("/{config_id}/disconnect-secondary")
async def disconnect_secondary(config_id: str):
    app_state.remove_secondary(config_id)
    return {"disconnected": True}


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
