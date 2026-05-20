import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .state import app_state

ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    app_state.add_ws(ws)

    try:
        initial_state = {
            "type": "init",
            "data": {
                "connection_state": (
                    app_state.connection_manager.state.value
                    if app_state.connection_manager
                    else "disconnected"
                ),
                "server_info": (
                    app_state.connection_manager.get_server_info().model_dump(mode="json")
                    if app_state.connection_manager and app_state.connection_manager.get_server_info()
                    else None
                ),
            },
        }
        await ws.send_text(json.dumps(initial_state, ensure_ascii=False, default=str))
    except Exception:
        pass

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")

            if msg_type == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        app_state.remove_ws(ws)
