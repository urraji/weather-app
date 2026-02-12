from __future__ import annotations

import logging
import sys
from typing import Any, Dict

import structlog

from app.correlation import get_request_id
from app.config import settings


def _add_request_id(_: Any, __: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Attach correlation id to every log event.

    Watched for:
      - Enables minimal request tracing in log search tools (CloudWatch/ELK/Loki).
      - Lets you correlate application logs with ALB/WAF logs using X-Request-ID.
    """
    rid = get_request_id()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def configure_logging() -> None:
    """Configure structured JSON logging for the service."""
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    structlog.configure(
        processors=[
            _add_request_id,
            structlog.stdlib.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.LOG_LEVEL, logging.INFO)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    logging.basicConfig(stream=sys.stdout, level=level)

    # Never log sensitive data (API keys). httpx can log full URLs at INFO/DEBUG.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)



def get_logger(name: str = "weather") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
