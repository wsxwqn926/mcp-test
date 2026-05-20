from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from backend.models.message_log import MessageLog, MessageFilter
from backend.utils.logger import get_logger

logger = get_logger("message_logger")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
HISTORY_DIR = DATA_DIR / "history"


class MessageLogger:
    def __init__(self):
        self._messages: list[MessageLog] = []

    def add(self, message: MessageLog) -> None:
        self._messages.append(message)

    def add_all(self, messages: list[MessageLog]) -> None:
        self._messages.extend(messages)

    def query(self, filter_params: MessageFilter | None = None) -> list[MessageLog]:
        if filter_params is None:
            return list(self._messages)

        result = self._messages
        if filter_params.session_id:
            result = [m for m in result if m.session_id == filter_params.session_id]
        if filter_params.direction:
            result = [m for m in result if m.direction == filter_params.direction]
        if filter_params.method:
            result = [m for m in result if m.method and filter_params.method in m.method]
        if filter_params.search_text:
            text = filter_params.search_text.lower()
            result = [
                m
                for m in result
                if text in json.dumps(m.data, ensure_ascii=False, default=str).lower()
            ]
        return result[-filter_params.limit :]

    def clear(self) -> None:
        self._messages.clear()

    @property
    def count(self) -> int:
        return len(self._messages)

    def get_stats(self) -> dict[str, Any]:
        requests = [m for m in self._messages if m.is_request()]
        responses = [m for m in self._messages if m.is_response()]
        notifications = [m for m in self._messages if m.is_notification()]
        errors = [m for m in self._messages if m.is_error_response()]
        durations = [m.duration_ms for m in responses if m.duration_ms is not None]

        return {
            "total": len(self._messages),
            "requests": len(requests),
            "responses": len(responses),
            "notifications": len(notifications),
            "errors": len(errors),
            "methods": list({m.method for m in self._messages if m.method}),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
        }

    def export_json(self) -> str:
        data = [m.model_dump(mode="json") for m in self._messages]
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    def export_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "timestamp", "direction", "method", "request_id",
            "duration_ms", "is_error", "data",
        ])
        for m in self._messages:
            writer.writerow([
                m.id,
                m.timestamp.isoformat(),
                m.direction,
                m.method or "",
                m.request_id or "",
                f"{m.duration_ms:.1f}" if m.duration_ms else "",
                "1" if m.is_error_response() else "0",
                json.dumps(m.data, ensure_ascii=False, default=str),
            ])
        return output.getvalue()

    def save_to_file(self, filepath: str | Path | None = None) -> str:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        if filepath is None:
            filepath = HISTORY_DIR / f"messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            filepath = Path(filepath)

        filepath.write_text(self.export_json(), encoding="utf-8")
        return str(filepath)
