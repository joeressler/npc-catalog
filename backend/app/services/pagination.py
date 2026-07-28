from collections.abc import Callable
from typing import Any, Generic, TypeVar

from fastapi import Request
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.config import settings

T = TypeVar("T")


class PaginatedEnvelope(BaseModel, Generic[T]):
    count: int
    next: str | None
    previous: str | None
    results: list[T]


def paginate_select(
    db: Session,
    request: Request,
    stmt: Select[Any],
    page: int,
    serialize: Callable[[Any], T],
    page_size: int | None = None,
    id_column: ColumnElement[Any] | None = None,
) -> PaginatedEnvelope[T]:
    size = page_size or settings.page_size
    page = max(page, 1)

    if id_column is not None:
        id_subq = stmt.with_only_columns(id_column).order_by(None).distinct().subquery()
        total = db.scalar(select(func.count()).select_from(id_subq)) or 0
        items = db.scalars(stmt.offset((page - 1) * size).limit(size)).unique().all()
    else:
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = db.scalar(count_stmt) or 0
        items = db.execute(stmt.offset((page - 1) * size).limit(size)).all()

    next_url, previous_url = _build_page_links(request, page, total, size)
    return PaginatedEnvelope(
        count=total,
        next=next_url,
        previous=previous_url,
        results=[serialize(item) for item in items],
    )


def _build_page_links(request: Request, page: int, total: int, page_size: int) -> tuple[str | None, str | None]:
    from urllib.parse import urlencode

    params = dict(request.query_params)
    base = str(request.url).split("?")[0]

    next_url = None
    if page * page_size < total:
        next_params = {**params, "page": str(page + 1)}
        next_url = f"{base}?{urlencode(next_params)}"

    previous_url = None
    if page > 1:
        prev_params = {**params, "page": str(page - 1)}
        previous_url = f"{base}?{urlencode(prev_params)}"

    return next_url, previous_url
