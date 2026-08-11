from collections.abc import Generator
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import Role, session_role, session_username
from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_current_username(request: Request) -> str:
    username = getattr(request.state, "username", None) or session_username(request)
    if username is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return username


def get_current_role(request: Request) -> Role:
    role = getattr(request.state, "role", None) or session_role(request)
    if role is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return role


CurrentUsername = Annotated[str, Depends(get_current_username)]
CurrentRole = Annotated[Role, Depends(get_current_role)]


def require_dm(role: CurrentRole) -> Literal["dm"]:
    if role != "dm":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="DM access required.")
    return "dm"


RequireDm = Annotated[Literal["dm"], Depends(require_dm)]
