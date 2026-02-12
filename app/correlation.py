from __future__ import annotations

import contextvars
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response

# Correlation id for minimal request tracing (logs + response header).
request_id_ctx_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_ctx_var.get()


async def correlation_id_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request_id_ctx_var.set(rid)
    resp = await call_next(request)
    resp.headers["X-Request-ID"] = rid
    return resp
