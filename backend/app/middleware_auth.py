"""HTTP middleware that gates /api and /media behind the session cookie."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.auth import is_public_path, requires_auth, session_username


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if is_public_path(request.method, path) or not requires_auth(path):
            return await call_next(request)

        if session_username(request) is None:
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)

        return await call_next(request)
