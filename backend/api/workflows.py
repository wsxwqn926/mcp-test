import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models.workflow import Workflow, WorkflowNode, WorkflowEdge, NodeType
from ..utils.workflow_config import load_workflows, save_workflow, delete_workflow
from .state import app_state

router = APIRouter()


@router.get("")
async def list_workflows():
    workflows = load_workflows()
    return {"workflows": {k: v.model_dump(mode="json") for k, v in workflows.items()}}


@router.post("")
async def create_workflow(body: dict):
    now = datetime.now()
    wf = Workflow(
        id=uuid.uuid4().hex,
        name=body.get("name", "未命名流程"),
        description=body.get("description"),
        tags=body.get("tags", []),
        variables=body.get("variables", {}),
        nodes=body.get("nodes", []),
        edges=body.get("edges", []),
        created_at=now,
        updated_at=now,
    )
    save_workflow(wf)
    return wf.model_dump(mode="json")


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    workflows = load_workflows()
    if workflow_id not in workflows:
        raise HTTPException(404, "Workflow not found")
    return workflows[workflow_id].model_dump(mode="json")


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, body: dict):
    workflows = load_workflows()
    if workflow_id not in workflows:
        raise HTTPException(404, "Workflow not found")
    wf = workflows[workflow_id]
    if "name" in body:
        wf.name = body["name"]
    if "description" in body:
        wf.description = body["description"]
    if "tags" in body:
        wf.tags = body["tags"]
    if "variables" in body:
        wf.variables = body["variables"]
    if "nodes" in body:
        wf.nodes = [WorkflowNode(**n) for n in body["nodes"]]
    if "edges" in body:
        wf.edges = [WorkflowEdge(**e) for e in body["edges"]]
    wf.updated_at = datetime.now()
    save_workflow(wf)
    return wf.model_dump(mode="json")


@router.delete("/{workflow_id}")
async def delete_workflow_route(workflow_id: str):
    workflows = load_workflows()
    if workflow_id not in workflows:
        raise HTTPException(404, "Workflow not found")
    delete_workflow(workflow_id)
    return {"deleted": True}


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str, body: dict = None):
    workflows = load_workflows()
    if workflow_id not in workflows:
        raise HTTPException(404, "Workflow not found")
    wf = workflows[workflow_id]

    if not app_state.list_connections():
        raise HTTPException(400, "No MCP connections active")

    from ..services.workflow_runner import WorkflowRunner
    runner = WorkflowRunner(app_state)
    initial_vars = (body or {}).get("variables")
    result = await runner.run(wf, initial_vars=initial_vars)
    app_state._last_workflow_results[workflow_id] = result
    return result.model_dump(mode="json")


@router.post("/{workflow_id}/stop")
async def stop_workflow(workflow_id: str):
    runner = getattr(app_state, "_active_runner", None)
    if runner:
        runner.request_stop()
    return {"stopped": True}


@router.get("/{workflow_id}/result")
async def get_workflow_result(workflow_id: str):
    results = getattr(app_state, "_last_workflow_results", {})
    if workflow_id not in results:
        return {"result": None}
    return {"result": results[workflow_id].model_dump(mode="json")}
