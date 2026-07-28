from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.mappers import serialize_session_detail, serialize_session_list
from app.models import GameSession, SessionNPC
from app.schemas import (
    SessionDetailRead,
    SessionWrite,
    SessionWritePartial,
    dump_session_partial,
)
from app.services.campaigns import get_campaign_or_404
from app.services.pagination import paginate_select
from app.services.sessions import (
    apply_session_write,
    get_session_or_404,
    next_session_number,
    sync_clues,
    sync_encounters,
    sync_npcs,
    sync_secrets,
    sync_story_paths,
)

router = APIRouter(tags=["sessions"])
campaign_sessions_router = APIRouter(prefix="/campaigns/{campaign_id}/sessions", tags=["sessions"])


@router.get("/sessions/{session_id}/", response_model=SessionDetailRead)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = get_session_or_404(db, session_id)
    return serialize_session_detail(session)


@router.patch("/sessions/{session_id}/", response_model=SessionDetailRead)
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
    if payload.npc_ids is not None:
        sync_npcs(db, session, payload.npc_ids)
    if payload.encounter_ids is not None:
        sync_encounters(db, session, payload.encounter_ids)

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
    npc_count = (
        select(func.count(SessionNPC.npc_id))
        .where(SessionNPC.session_id == GameSession.id)
        .scalar_subquery()
    )
    stmt = (
        select(GameSession, npc_count.label("npc_count"))
        .where(GameSession.campaign_id == campaign_id)
        .order_by(GameSession.number.asc())
    )

    def serialize(row: tuple[GameSession, int]) -> dict:
        session, count = row[0], row[1]
        return serialize_session_list(session, npc_count=count).model_dump()

    return paginate_select(db, request, stmt, page, serialize)


@campaign_sessions_router.post("/", status_code=status.HTTP_201_CREATED, response_model=SessionDetailRead)
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
    sync_npcs(db, session, payload.npc_ids)
    sync_encounters(db, session, payload.encounter_ids)
    db.commit()
    session = get_session_or_404(db, session.id)
    return serialize_session_detail(session)
