from __future__ import annotations

import json
from typing import Any


def format_json(data: dict[str, Any] | list[Any] | str, indent: int = 2) -> str:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return data
    return json.dumps(data, ensure_ascii=False, indent=indent, default=str)


def validate_json(text: str) -> tuple[bool, str]:
    try:
        json.loads(text)
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"JSON 鐟欙絾鐎介柨娆掝嚖 (鐞?{e.lineno}, 閸?{e.colno}): {e.msg}"


def extract_json_from_text(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    if start == -1:
        start = text.find("[")
    if start == -1:
        return None
    try:
        return json.loads(text[start:])
    except json.JSONDecodeError:
        return None
