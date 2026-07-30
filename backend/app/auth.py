"""Env-credential session cookies for the single-user login gate."""

from __future__ import annotations

import hashlib
import hmac
import threading
import time
from collections import defaultdict
from typing import Final

from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

COOKIE_NAME: Final = "npc_session"
SESSION_MAX_AGE_SECONDS: Final = 60 * 60 * 24 * 14  # 14 days
COOKIE_SAMESITE: Final = "lax"

# In-process login lockout (defense if backend port is ever published).
LOGIN_MAX_FAILURES: Final = 10
LOGIN_WINDOW_SECONDS: Final = 60
LOGIN_LOCKOUT_SECONDS: Final = 60

_login_failures: dict[str, list[float]] = defaultdict(list)
_login_lock = threading.Lock()


def _signing_key() -> bytes:
    secret = settings.auth_secret.strip() or "dev-secret-change-me"
    return secret.encode("utf-8")


def create_session_token(username: str) -> str:
    expires_at = int(time.time()) + SESSION_MAX_AGE_SECONDS
    payload = f"{username}:{expires_at}"
    signature = hmac.new(_signing_key(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"


def verify_session_token(token: str | None) -> str | None:
    if not token:
        return None
    parts = token.split(":")
    if len(parts) != 3:
        return None
    username, expires_raw, signature = parts
    try:
        expires_at = int(expires_raw)
    except ValueError:
        return None
    if expires_at < int(time.time()):
        return None
    payload = f"{username}:{expires_raw}"
    expected = hmac.new(_signing_key(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    if not hmac.compare_digest(username, settings.auth_username):
        return None
    return username


def _fixed_digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def credentials_match(username: str, password: str) -> bool:
    expected_user = settings.auth_username
    expected_pass = settings.auth_password
    if not expected_user or not expected_pass:
        return False
    # Hash first so compare_digest stays constant-time across unequal lengths.
    user_ok = hmac.compare_digest(_fixed_digest(username), _fixed_digest(expected_user))
    pass_ok = hmac.compare_digest(_fixed_digest(password), _fixed_digest(expected_pass))
    return user_ok and pass_ok


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _failure_key(ip: str, username: str) -> str:
    return f"{ip}|{username.strip().lower()}"


def login_is_locked(ip: str, username: str) -> bool:
    key = _failure_key(ip, username)
    now = time.time()
    with _login_lock:
        stamps = [t for t in _login_failures[key] if now - t < LOGIN_WINDOW_SECONDS]
        _login_failures[key] = stamps
        if len(stamps) < LOGIN_MAX_FAILURES:
            return False
        oldest = min(stamps)
        return (now - oldest) < LOGIN_LOCKOUT_SECONDS


def record_login_failure(ip: str, username: str) -> None:
    key = _failure_key(ip, username)
    now = time.time()
    with _login_lock:
        stamps = [t for t in _login_failures[key] if now - t < LOGIN_WINDOW_SECONDS]
        stamps.append(now)
        _login_failures[key] = stamps


def clear_login_failures(ip: str, username: str) -> None:
    key = _failure_key(ip, username)
    with _login_lock:
        _login_failures.pop(key, None)


def set_session_cookie(response: Response, username: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_session_token(username),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=settings.auth_cookie_secure,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=settings.auth_cookie_secure,
    )


def session_username(request: Request) -> str | None:
    return verify_session_token(request.cookies.get(COOKIE_NAME))


def is_public_path(method: str, path: str) -> bool:
    if method == "OPTIONS":
        return True
    if path == "/health":
        return True
    if path in {"/api/auth/login", "/api/auth/login/", "/api/auth/logout", "/api/auth/logout/"}:
        return True
    return False


def requires_auth(path: str) -> bool:
    return path.startswith("/api/") or path.startswith("/media/")
