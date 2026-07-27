from fastapi import HTTPException, status
from sqlalchemy import Select, delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Encounter, GameSession, Location, NPC, SessionBeat, SessionClue, SessionSecret, SessionStoryPath
from app.schemas import SessionStoryPathWrite


def _clean_line_items(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item.strip()]


def sync_story_paths(db: Session, session: GameSession, paths: list[SessionStoryPathWrite]) -> None:
    path_ids = db.scalars(
        select(SessionStoryPath.id).where(SessionStoryPath.session_id == session.id)
    ).all()
    if path_ids:
        db.execute(delete(SessionBeat).where(SessionBeat.path_id.in_(path_ids)))
    db.execute(delete(SessionStoryPath).where(SessionStoryPath.session_id == session.id))
    for path_order, path_data in enumerate(paths):
        name = path_data.name.strip()
        if not name:
            continue
        path = SessionStoryPath(session_id=session.id, name=name, sort_order=path_order)
        db.add(path)
        db.flush()
        for beat_order, text in enumerate(_clean_line_items(path_data.beats)):
            db.add(SessionBeat(path_id=path.id, text=text, sort_order=beat_order))


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


def sync_encounters(db: Session, session: GameSession, encounter_ids: list[int]) -> None:
    if not encounter_ids:
        session.encounters = []
        return

    unique_ids: list[int] = []
    seen: set[int] = set()
    for encounter_id in encounter_ids:
        if encounter_id not in seen:
            seen.add(encounter_id)
            unique_ids.append(encounter_id)

    encounters = db.scalars(select(Encounter).where(Encounter.id.in_(unique_ids))).all()
    encounter_map = {encounter.id: encounter for encounter in encounters}
    if len(encounter_map) != len(unique_ids):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="One or more encounters not found.")

    for encounter in encounters:
        if encounter.campaign_id != session.campaign_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Encounters must belong to the session's campaign.",
            )

    session.encounters = [encounter_map[encounter_id] for encounter_id in unique_ids]


def sync_locations(db: Session, session: GameSession, location_ids: list[int]) -> None:
    if not location_ids:
        session.locations = []
        return

    unique_ids: list[int] = []
    seen: set[int] = set()
    for location_id in location_ids:
        if location_id not in seen:
            seen.add(location_id)
            unique_ids.append(location_id)

    locations = db.scalars(select(Location).where(Location.id.in_(unique_ids))).all()
    location_map = {location.id: location for location in locations}
    if len(location_map) != len(unique_ids):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="One or more locations not found.")

    for location in locations:
        if location.campaign_id != session.campaign_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Locations must belong to the session's campaign.",
            )

    session.locations = [location_map[location_id] for location_id in unique_ids]


def session_query_options(stmt: Select[tuple[GameSession]]) -> Select[tuple[GameSession]]:
    return stmt.options(
        selectinload(GameSession.story_paths).selectinload(SessionStoryPath.beats),
        selectinload(GameSession.clues),
        selectinload(GameSession.secrets),
        selectinload(GameSession.characters),
        selectinload(GameSession.encounters),
        selectinload(GameSession.locations),
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
