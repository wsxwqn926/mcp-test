from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.state import app_state
from backend.api.router import api_router
from backend.api.ws import ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_state.set_loop(asyncio.get_running_loop())
    yield
    if app_state.connection_manager and app_state.is_connected:
        try:
            await app_state.connection_manager.disconnect()
        except Exception:
            pass


import asyncio

app = FastAPI(
    title="MCP Test Tool",
    version="0.2.0",
    description="MCP Server Test Tool - Backend API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
