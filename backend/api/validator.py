from fastapi import APIRouter, HTTPException

from ..services.protocol_validator import ProtocolValidator
from .state import app_state

router = APIRouter()


@router.post("/run")
async def run_validation():
    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")

    validator = ProtocolValidator(wrapper)
    report = await validator.run_validation()
    return report.model_dump(mode="json")
