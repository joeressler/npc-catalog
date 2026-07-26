from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import GameSession, SessionNPC
from app.schemas import SessionWrite, SessionWritePartial, dump_session_partial
from app.serializers import serialize_session_detail, serialize_session_list
from app.services.npcs import get_campaign_or_404
from app.services.pagination import paginate_select
from app.services.sessions import (
    apply_session_write,
    get_session_or_404,
    next_session_number,
    session_query_options,
    sync_story_paths,
    sync_characters,
    sync_clues,
    sync_secrets,
)

router = APIRouter(tags=["sessions"])
campaign_sessions_router = APIRouter(prefix="/campaigns/{campaign_id}/sessions", tags=["sessions"])


@router.get("/sessions/{session_id}/")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = get_session_or_404(db, session_id)
    return serialize_session_detail(session)


@router.patch("/sessions/{session_id}/")
def update_session(session_id: int, payload: SessionWritePartial, db: Session = Depends(get_db)):
    session = get_session_or_404(db, session_id)
    data = dump_session_partial(payload)

    apply_session_write(
        db,
        session,
        number=data.get("number"),
        title=data.get("title"),
        overall_notes=data.get("overall_notes"),
        partial=True,
    )

    if payload.story_paths is not None:
        sync_story_paths(db, session, payload.story_paths)
    if payload.clues is not None:
        sync_clues(db, session, payload.clues)
    if payload.secrets is not None:
        sync_secrets(db, session, payload.secrets)
    if payload.character_ids is not None:
        sync_characters(db, session, payload.character_ids)

    db.commit()
    session = get_session_or_404(db, session_id)
    return serialize_session_detail(session)


@router.delete("/sessions/{session_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = get_session_or_404(db, session_id)
    db.delete(session)
    db.commit()


@campaign_sessions_router.get("/")
def list_campaign_sessions(
    campaign_id: int,
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    character_count = (
        select(func.count(SessionNPC.npc_id))
        .where(SessionNPC.session_id == GameSession.id)
        .scalar_subquery()
    )
    stmt = (
        select(GameSession, character_count.label("character_count"))
        .where(GameSession.campaign_id == campaign_id)
        .order_by(GameSession.number.asc())
    )

    def serialize(row: tuple[GameSession, int]) -> dict:
        session, count = row[0], row[1]
        return serialize_session_list(session, character_count=count).model_dump()

    return paginate_select(db, request, stmt, page, serialize)


@campaign_sessions_router.post("/", status_code=status.HTTP_201_CREATED)
def create_campaign_session(
    campaign_id: int,
    payload: SessionWrite,
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    number = payload.number if payload.number is not None else next_session_number(db, campaign_id)

    session = GameSession(campaign_id=campaign_id, number=number)
    apply_session_write(
        db,
        session,
        number=number,
        title=payload.title,
        overall_notes=payload.overall_notes,
        partial=False,
    )
    db.add(session)
    db.flush()
    sync_story_paths(db, session, payload.story_paths)
    sync_clues(db, session, payload.clues)
    sync_secrets(db, session, payload.secrets)
    sync_characters(db, session, payload.character_ids)
    db.commit()
    session = get_session_or_404(db, session.id)
    return serialize_session_detail(session)
