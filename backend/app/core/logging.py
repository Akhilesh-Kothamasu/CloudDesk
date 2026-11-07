"""Structured JSON logging with request_id and workflow_id context.

Outputs valid JSON on every log line with request_id and workflow_id fields
(rendered as null when unset).
"""

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import sys
from typing import Any, Generator

# Context variables for tracing request and workflow IDs across async flows
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_workflow_id_ctx: ContextVar[str | None] = ContextVar("workflow_id", default=None)

# Standard LogRecord attributes to ignore when extracting custom extra fields
_STANDARD_RECORD_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


def get_request_id() -> str | None:
    """Return the current context request_id or None."""
    return _request_id_ctx.get()


def set_request_id(request_id: str | None) -> None:
    """Set the current context request_id."""
    _request_id_ctx.set(request_id)


def get_workflow_id() -> str | None:
    """Return the current context workflow_id or None."""
    return _workflow_id_ctx.get()


def set_workflow_id(workflow_id: str | None) -> None:
    """Set the current context workflow_id."""
    _workflow_id_ctx.set(workflow_id)


@contextmanager
def log_context(
    request_id: str | None = None,
    workflow_id: str | None = None,
) -> Generator[None, None, None]:
    """Context manager to bind request_id and/or workflow_id to the current execution context."""
    req_token = None
    wf_token = None

    if request_id is not None:
        req_token = _request_id_ctx.set(request_id)
    if workflow_id is not None:
        wf_token = _workflow_id_ctx.set(workflow_id)

    try:
        yield
    finally:
        if req_token is not None:
            _request_id_ctx.reset(req_token)
        if wf_token is not None:
            _workflow_id_ctx.reset(wf_token)


class JSONFormatter(logging.Formatter):
    """Formats LogRecord instances as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        # Determine request_id and workflow_id (record extra takes precedence over contextvar)
        req_id = getattr(record, "request_id", None)
        if req_id is None:
            req_id = get_request_id()

        wf_id = getattr(record, "workflow_id", None)
        if wf_id is None:
            wf_id = get_workflow_id()

        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": req_id,
            "workflow_id": wf_id,
        }

        # Include formatted exception traceback if available
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Merge any custom extra attributes passed to logger call
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS and key not in payload:
                payload[key] = value

        return json.dumps(payload, default=str)


def setup_logging(log_level: str | int | None = None) -> None:
    """Initialize root logger with JSONFormatter on stdout.

    Args:
        log_level: Optional log level name or integer. If None, reads from
                   application settings LOG_LEVEL.
    """
    if log_level is None:
        try:
            from backend.app.core.config import get_settings

            log_level = get_settings().LOG_LEVEL
        except Exception:
            log_level = "INFO"

    if isinstance(log_level, str):
        level_no = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level_no = log_level

    root_logger = logging.getLogger()
    root_logger.setLevel(level_no)

    # Remove existing handlers to prevent duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level_no)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)


def get_logger(name: str = "clouddesk") -> logging.Logger:
    """Return a logger configured for the application."""
    return logging.getLogger(name)

