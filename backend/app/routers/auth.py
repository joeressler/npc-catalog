from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from app.auth import (
    clear_login_failures,
    clear_session_cookie,
    client_ip,
    credentials_match,
    login_is_locked,
    record_login_failure,
    role_for_username,
    session_username,
    set_session_cookie,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


@router.post("/login/")
def login(payload: LoginRequest, request: Request, response: Response):
    ip = client_ip(request)
    if login_is_locked(ip, payload.username):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many failed login attempts. Try again shortly."},
            headers={"Retry-After": "60"},
        )
    if not credentials_match(payload.username, payload.password):
        record_login_failure(ip, payload.username)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid username or password"},
        )
    clear_login_failures(ip, payload.username)
    set_session_cookie(response, payload.username)
    role = role_for_username(payload.username)
    return {"username": payload.username, "role": role}


@router.post("/logout/")
def logout(response: Response):
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/me/")
def me(request: Request):
    username = session_username(request)
    if username is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Not authenticated"},
        )
    return {"username": username, "role": role_for_username(username)}
