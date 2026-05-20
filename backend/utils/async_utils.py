from __future__ import annotations

import asyncio
import threading
import sys
from concurrent.futures import Future
from typing import Any, Coroutine, TypeVar

T = TypeVar("T")

_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop, _loop_thread
    if _loop is None or _loop.is_closed():
        if sys.platform == "win32":
            _loop = asyncio.ProactorEventLoop()
        else:
            _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)

        _loop_thread = threading.Thread(target=_loop.run_forever, daemon=True)
        _loop_thread.start()

    return _loop


def run_async(coro: Coroutine[Any, Any, T], timeout: float = 60.0) -> T:
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=timeout)
