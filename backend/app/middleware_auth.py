"""HTTP middleware that gates /api and /media behind the session cookie."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.auth import (
    is_public_path,
    player_may_mutate,
    requires_auth,
    role_for_username,
    session_username,
)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if is_public_path(request.method, path) or not requires_auth(path):
            return await call_next(request)

        username = session_username(request)
        if username is None:
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)

        role = role_for_username(username)
        request.state.username = username
        request.state.role = role

        if role == "player" and not player_may_mutate(request.method, path):
            return JSONResponse({"detail": "Players have readonly access."}, status_code=403)

        return await call_next(request)
