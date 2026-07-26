from fastapi import HTTPException, status
from sqlalchemy import Select, delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import GameSession, NPC, SessionBeat, SessionClue, SessionSecret


def _clean_line_items(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item.strip()]


def sync_beats(db: Session, session: GameSession, texts: list[str]) -> None:
    db.execute(delete(SessionBeat).where(SessionBeat.session_id == session.id))
    for sort_order, text in enumerate(_clean_line_items(texts)):
        db.add(SessionBeat(session_id=session.id, text=text, sort_order=sort_order))


def sync_clues(db: Session, session: GameSession, texts: list[str]) -> None:
    db.execute(delete(SessionClue).where(SessionClue.session_id == session.id))
    for sort_order, text in enumerate(_clean_line_items(texts)):
        db.add(SessionClue(session_id=session.id, text=text, sort_order=sort_order))


def sync_secrets(db: Session, session: GameSession, texts: list[str]) -> None:
    db.execute(delete(SessionSecret).where(SessionSecret.session_id == session.id))
    for sort_order, text in enumerate(_clean_line_items(texts)):
        db.add(SessionSecret(session_id=session.id, text=text, sort_order=sort_order))


def sync_characters(db: Session, session: GameSession, character_ids: list[int]) -> None:
    if not character_ids:
        session.characters = []
        return

    unique_ids: list[int] = []
    seen: set[int] = set()
    for character_id in character_ids:
        if character_id not in seen:
            seen.add(character_id)
            unique_ids.append(character_id)

    npcs = db.scalars(select(NPC).where(NPC.id.in_(unique_ids))).all()
    npc_map = {npc.id: npc for npc in npcs}
    if len(npc_map) != len(unique_ids):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="One or more characters not found.")

    for npc in npcs:
        if npc.campaign_id != session.campaign_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Characters must belong to the session's campaign.",
            )

    session.characters = [npc_map[character_id] for character_id in unique_ids]


def session_query_options(stmt: Select[tuple[GameSession]]) -> Select[tuple[GameSession]]:
    return stmt.options(
        selectinload(GameSession.beats),
        selectinload(GameSession.clues),
        selectinload(GameSession.secrets),
        selectinload(GameSession.characters),
    )


def next_session_number(db: Session, campaign_id: int) -> int:
    max_number = db.scalar(
        select(func.max(GameSession.number)).where(GameSession.campaign_id == campaign_id)
    )
    return (max_number or 0) + 1


def ensure_unique_session_number(
    db: Session,
    *,
    campaign_id: int,
    number: int,
    exclude_session_id: int | None = None,
) -> None:
    stmt = select(GameSession).where(
        GameSession.campaign_id == campaign_id,
        GameSession.number == number,
    )
    if exclude_session_id is not None:
        stmt = stmt.where(GameSession.id != exclude_session_id)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Session number {number} already exists in this campaign.",
        )


def get_session_or_404(db: Session, session_id: int) -> GameSession:
    session = db.scalar(session_query_options(select(GameSession).where(GameSession.id == session_id)))
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return session


def apply_session_write(
    db: Session,
    session: GameSession,
    *,
    number: int | None,
    title: str | None = None,
    overall_notes: str | None = None,
    partial: bool = False,
) -> None:
    if number is not None:
        ensure_unique_session_number(
            db,
            campaign_id=session.campaign_id,
            number=number,
            exclude_session_id=session.id,
        )
        session.number = number
    elif not partial and session.number is None:
        session.number = next_session_number(db, session.campaign_id)

    if title is not None or not partial:
        session.title = (title or "").strip() if title is not None else session.title
    if overall_notes is not None or not partial:
        session.overall_notes = overall_notes if overall_notes is not None else session.overall_notes
