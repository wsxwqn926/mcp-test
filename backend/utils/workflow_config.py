from __future__ import annotations

import json
from pathlib import Path

from ..models.workflow import Workflow
from ..utils.logger import get_logger

logger = get_logger("workflow_config")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
WORKFLOWS_FILE = DATA_DIR / "workflows.json"


def _ensure_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not WORKFLOWS_FILE.exists():
        WORKFLOWS_FILE.write_text("[]", encoding="utf-8")


def load_workflows() -> dict[str, Workflow]:
    _ensure_file()
    try:
        raw = json.loads(WORKFLOWS_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return {wf["id"]: Workflow(**wf) for wf in raw if "id" in wf}
        return {}
    except Exception:
        return {}


def save_workflow(workflow: Workflow):
    _ensure_file()
    workflows = load_workflows()
    workflows[workflow.id] = workflow
    _write_all(workflows)


def delete_workflow(workflow_id: str):
    workflows = load_workflows()
    workflows.pop(workflow_id, None)
    _write_all(workflows)


def _write_all(workflows: dict[str, Workflow]):
    data = [wf.model_dump(mode="json") for wf in workflows.values()]
    WORKFLOWS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
