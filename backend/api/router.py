from fastapi import APIRouter

from .connections import router as connections_router
from .tools import router as tools_router
from .resources import router as resources_router
from .prompts import router as prompts_router
from .messages import router as messages_router
from .tests import router as tests_router
from .validator import router as validator_router
from .performance import router as performance_router

api_router = APIRouter()

api_router.include_router(connections_router, prefix="/connections", tags=["connections"])
api_router.include_router(tools_router, prefix="/tools", tags=["tools"])
api_router.include_router(resources_router, prefix="/resources", tags=["resources"])
api_router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
api_router.include_router(tests_router, prefix="/tests", tags=["tests"])
api_router.include_router(validator_router, prefix="/validator", tags=["validator"])
api_router.include_router(performance_router, prefix="/performance", tags=["performance"])
