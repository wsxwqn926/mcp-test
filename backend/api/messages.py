from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..models.message_log import MessageFilter
from .state import app_state

router = APIRouter()


@router.get("")
async def query_messages(
    direction: str = None,
    method: str = None,
    search_text: str = None,
    limit: int = 500,
):
    f = MessageFilter(
        direction=direction,
        method=method,
        search_text=search_text,
        limit=limit,
    )
    messages = app_state.message_logger.query(f)
    return {
        "messages": [m.model_dump(mode="json") for m in messages],
        "total": app_state.message_logger.count,
    }


@router.get("/stats")
async def message_stats():
    return app_state.message_logger.get_stats()


@router.delete("")
async def clear_messages():
    app_state.message_logger.clear()
    return {"cleared": True}


@router.get("/export/json")
async def export_json():
    data = app_state.message_logger.export_json()
    return Response(content=data, media_type="application/json")


@router.get("/export/csv")
async def export_csv():
    data = app_state.message_logger.export_csv()
    return Response(content=data, media_type="text/csv")


@router.get("/history")
async def list_history():
    history_dir = Path("data/history")
    if not history_dir.exists():
        return {"files": []}
    files = sorted(history_dir.glob("messages_*.json"), reverse=True)
    return {
        "files": [
            {
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            }
            for f in files[:50]
        ]
    }


@router.get("/history/{filename}")
async def get_history(filename: str):
    if ".." in filename or "/" in filename:
        raise HTTPException(400, "Invalid filename")
    filepath = Path("data/history") / filename
    if not filepath.exists():
        raise HTTPException(404, "History file not found")
    data = filepath.read_text(encoding="utf-8")
    return Response(content=data, media_type="application/json")
