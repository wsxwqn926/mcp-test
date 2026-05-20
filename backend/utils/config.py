from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel

from backend.models.server_config import ServerConfig

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CONFIG_FILE = DATA_DIR / "server_configs.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_server_configs() -> dict[str, ServerConfig]:
    _ensure_data_dir()
    if not CONFIG_FILE.exists():
        return {}
    raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {item["id"]: ServerConfig(**item) for item in raw}


def save_server_configs(configs: dict[str, ServerConfig]) -> None:
    _ensure_data_dir()
    items = [config.model_dump(mode="json") for config in configs.values()]
    CONFIG_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def save_server_config(config: ServerConfig) -> None:
    configs = load_server_configs()
    configs[config.id] = config
    save_server_configs(configs)


def delete_server_config(config_id: str) -> None:
    configs = load_server_configs()
    configs.pop(config_id, None)
    save_server_configs(configs)
