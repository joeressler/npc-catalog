from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from app.auth import (
    clear_session_cookie,
    credentials_match,
    session_username,
    set_session_cookie,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


@router.post("/login/")
def login(payload: LoginRequest, response: Response):
    if not credentials_match(payload.username, payload.password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid username or password"},
        )
    set_session_cookie(response, payload.username)
    return {"username": payload.username}


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
    return {"username": username}
