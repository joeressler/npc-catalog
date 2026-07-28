from fastapi import APIRouter, Request
from sqlalchemy import select

from app.deps import DbSession
from app.models import Tag
from app.schemas import TagRead
from app.services.pagination import paginate_select

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/")
def list_tags(
    request: Request,
    db: DbSession,
    page: int = 1,
):
    stmt = select(Tag).order_by(Tag.name.asc())
    return paginate_select(
        db,
        request,
        stmt,
        page,
        lambda tag: TagRead.model_validate(tag).model_dump(),
        id_column=Tag.id,
    )
