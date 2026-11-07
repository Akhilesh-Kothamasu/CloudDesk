"""Request ID middleware for CloudDesk.

Echoes safe client-supplied X-Request-ID or generates a UUID4.
Binds request_id to logging context and ensures X-Request-ID header is present
on all responses.
"""

import re
from typing import Callable
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.app.core.logging import log_context

# Safe request ID pattern: 1-128 characters of alphanumeric, dot, underscore, colon, hyphen
_SAFE_REQUEST_ID_REGEX = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def is_safe_request_id(value: str | None) -> bool:
    """Validate whether request ID conforms to safe character set and length."""
    if not value or not isinstance(value, str):
        return False
    return bool(_SAFE_REQUEST_ID_REGEX.fullmatch(value))


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to assign or validate X-Request-ID on all incoming requests."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        incoming_id = request.headers.get("X-Request-ID")
        if incoming_id and is_safe_request_id(incoming_id):
            request_id = incoming_id
        else:
            request_id = str(uuid.uuid4())

        # Store in request state for downstream handlers
        request.state.request_id = request_id

        # Bind to structured logging context for the duration of the request
        with log_context(request_id=request_id):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

