"""Generic async retry utility with exponential backoff."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable: tuple[type[Exception], ...] = (OSError, TimeoutError, ConnectionError),
    **kwargs,
) -> T:
    """Execute an async callable with exponential backoff retry.

    Args:
        func: The async callable to execute.
        *args: Positional arguments forwarded to *func*.
        max_retries: Maximum number of retries (total attempts = max_retries + 1).
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        retryable: Exception types that trigger a retry; all others propagate immediately.
        **kwargs: Keyword arguments forwarded to *func*.

    Raises:
        The last exception raised if all retries are exhausted.
    """
    last_exc: Exception
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retryable as exc:
            last_exc = exc
            if attempt == max_retries:
                break
            delay = min(base_delay * (2**attempt), max_delay)
            logger.warning(
                "Attempt %d/%d failed (%s: %s). Retrying in %.1fs.",
                attempt + 1,
                max_retries,
                type(exc).__name__,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
    raise last_exc  # type: ignore[possibly-undefined]
