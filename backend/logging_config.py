"""Structured JSON logging for the backend.

Every record is emitted as a single line of JSON with stable keys so logs
ship cleanly to Loki/Datadog/CloudWatch without further parsing. The
``setup_logging`` function is idempotent so it is safe to call from both the
FastAPI lifespan and from tests.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

_RESERVED = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """Format every record as one line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            try:
                json.dumps(value)
            except TypeError:
                value = repr(value)
            payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_CONFIGURED = False


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging with a JSON formatter. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Tame noisy libraries.
    for noisy in ("uvicorn.access", "uvicorn.error", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True
