from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Tag
from app.schemas import TagRead
from app.services.pagination import paginate_select

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/")
def list_tags(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
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
