from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException

from ..models.test_case import TestCase, TestStep, StepType, Assertion, AssertionType
from ..models.test_result import TestRunResult
from ..services.test_runner import TestRunner
from ..utils.test_config import load_test_cases, save_test_case, delete_test_case as _delete_tc
from .state import app_state

router = APIRouter()


@router.get("")
async def list_tests():
    cases = load_test_cases()
    return {
        "test_cases": {k: v.model_dump(mode="json") for k, v in cases.items()}
    }


@router.post("")
async def create_test(body: dict):
    case = _build_test_case(body)
    save_test_case(case)
    return case.model_dump(mode="json")


@router.get("/{test_id}")
async def get_test(test_id: str):
    cases = load_test_cases()
    if test_id not in cases:
        raise HTTPException(404, "Test case not found")
    return cases[test_id].model_dump(mode="json")


@router.put("/{test_id}")
async def update_test(test_id: str, body: dict):
    cases = load_test_cases()
    if test_id not in cases:
        raise HTTPException(404, "Test case not found")
    case = _build_test_case(body, test_id)
    save_test_case(case)
    return case.model_dump(mode="json")


@router.delete("/{test_id}")
async def delete_test(test_id: str):
    cases = load_test_cases()
    if test_id not in cases:
        raise HTTPException(404, "Test case not found")
    _delete_tc(test_id)
    return {"deleted": True}


@router.post("/{test_id}/run")
async def run_test(test_id: str):
    cases = load_test_cases()
    if test_id not in cases:
        raise HTTPException(404, "Test case not found")

    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")

    runner = TestRunner(wrapper)
    result = await runner.run_test(cases[test_id])
    return result.model_dump(mode="json")


@router.post("/record")
async def record_from_history(body: dict = None):
    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")

    from ..services.tool_service import ToolService

    tool_svc = ToolService(wrapper)
    history = tool_svc.get_call_history()

    if not history:
        return {"steps": [], "message": "No call history available"}

    steps = []
    for i, h in enumerate(history):
        steps.append(TestStep(
            id=f"step-{i * 2 + 1}",
            type=StepType.TOOL_CALL,
            name=f"Call {h.tool_name}",
            tool_name=h.tool_name,
            arguments=h.arguments,
        ))
        steps.append(TestStep(
            id=f"step-{i * 2 + 2}",
            type=StepType.ASSERTION,
            name="Assert success",
            assertion=Assertion(type=AssertionType.STATUS_SUCCESS),
        ))

    return {
        "steps": [s.model_dump(mode="json") for s in steps],
        "count": len(steps),
    }


def _build_test_case(body: dict, test_id: str | None = None) -> TestCase:
    now = datetime.now()
    steps = []
    for s in body.get("steps", []):
        assertion = None
        if s.get("assertion"):
            a = s["assertion"]
            assertion = Assertion(
                type=AssertionType(a["type"]),
                expected=a.get("expected"),
                path=a.get("path"),
                negate=a.get("negate", False),
            )
        steps.append(TestStep(
            id=s.get("id", str(uuid.uuid4())),
            type=StepType(s["type"]),
            name=s.get("name", ""),
            tool_name=s.get("tool_name"),
            arguments=s.get("arguments"),
            resource_uri=s.get("resource_uri"),
            prompt_name=s.get("prompt_name"),
            prompt_arguments=s.get("prompt_arguments"),
            assertion=assertion,
            wait_seconds=s.get("wait_seconds"),
        ))

    return TestCase(
        id=test_id or body.get("id", str(uuid.uuid4())),
        name=body.get("name", "Unnamed Test"),
        description=body.get("description"),
        server_config_id=body.get("server_config_id", ""),
        steps=steps,
        tags=body.get("tags", []),
        created_at=body.get("created_at", now),
        updated_at=now,
    )
