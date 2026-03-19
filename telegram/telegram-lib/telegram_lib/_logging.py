"""
Logging decorator for telegram-lib wrapper functions (T4, T5).

Every public function is decorated so that it automatically logs:
  - input parameters and start timestamp  (before execution)
  - result summary and end timestamp       (after execution)

Callers control verbosity through the standard Python ``logging`` module
(T5) — no custom log configuration is required.
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger("telegram_lib")


def logged(fn: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
    """Decorator that wraps an async function with entry/exit logging (T4).

    Logs at DEBUG level so that callers can enable it selectively.
    """

    @functools.wraps(fn)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.monotonic()
        start_ts = datetime.now(tz=UTC).isoformat()

        # Build a safe representation of arguments (skip the TelegramClient object)
        safe_kwargs = {k: v for k, v in kwargs.items() if k != "client"}
        logger.debug(
            "[%s] START at %s | args=%s kwargs=%s",
            fn.__qualname__,
            start_ts,
            args[1:],  # skip 'client' positional arg
            safe_kwargs,
        )

        result = await fn(*args, **kwargs)

        elapsed_ms = (time.monotonic() - start) * 1000
        end_ts = datetime.now(tz=UTC).isoformat()
        logger.debug(
            "[%s] END   at %s | elapsed=%.1fms | result_type=%s",
            fn.__qualname__,
            end_ts,
            elapsed_ms,
            type(result).__name__,
        )
        return result

    return wrapper
