import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from structlog import contextvars
from app.metrics import http_requests_total, http_request_duration_seconds

class CorrelationAndMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get('x-request-id') or str(uuid.uuid4())
        contextvars.clear_contextvars()
        contextvars.bind_contextvars(request_id=rid)

        start = time.time()
        path = request.url.path
        method = request.method

        response = await call_next(request)
        status = str(response.status_code)

        http_requests_total.labels(path, method, status).inc()
        http_request_duration_seconds.labels(path, method).observe(time.time() - start)

        response.headers['x-request-id'] = rid
        return response
