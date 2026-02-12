from __future__ import annotations

import contextvars
import uuid
from typing import Callable, Awaitable

from fastapi import Request, Response

# Per-request correlation id. Used for minimal request tracing across logs/services.
request_id_ctx_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_ctx_var.get()


async def correlation_id_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Ensure every request has a correlation id.

    Behavior:
      - If client sends X-Request-ID, reuse it.
      - Otherwise generate a UUID4.
      - Store it in a ContextVar for use in logs and downstream calls.
      - Always echo it back in the response headers for debugging.
    """
    req_id = request.headers.get("X-Request-ID")
    if not req_id:
        req_id = str(uuid.uuid4())

    request_id_ctx_var.set(req_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response
