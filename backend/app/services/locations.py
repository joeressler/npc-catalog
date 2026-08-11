from fastapi import HTTPException, status
from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session, selectinload

from app.models import NPC, Location, LocationLoot, LocationObject
from app.schemas import LocationObjectWrite


def _clean_line_items(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item.strip()]


def sync_loot(db: Session, location: Location, texts: list[str]) -> None:
    db.execute(delete(LocationLoot).where(LocationLoot.location_id == location.id))
    for sort_order, text in enumerate(_clean_line_items(texts)):
        db.add(LocationLoot(location_id=location.id, description=text, sort_order=sort_order))


def sync_objects(db: Session, location: Location, objects: list[LocationObjectWrite]) -> None:
    db.execute(delete(LocationObject).where(LocationObject.location_id == location.id))
    for sort_order, obj in enumerate(objects):
        name = obj.name.strip()
        if not name:
            continue
        db.add(
            LocationObject(
                location_id=location.id,
                name=name,
                description=obj.description.strip() if obj.description else "",
                sort_order=sort_order,
            )
        )


def sync_npcs(db: Session, location: Location, npc_ids: list[int]) -> None:
    if not npc_ids:
        location.npcs = []
        return

    unique_ids: list[int] = []
    seen: set[int] = set()
    for npc_id in npc_ids:
        if npc_id not in seen:
            seen.add(npc_id)
            unique_ids.append(npc_id)

    npcs = db.scalars(select(NPC).where(NPC.id.in_(unique_ids))).all()
    npc_map = {npc.id: npc for npc in npcs}
    if len(npc_map) != len(unique_ids):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="One or more NPCs not found.")

    for npc in npcs:
        if npc.campaign_id != location.campaign_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="NPCs must belong to the location's campaign.",
            )

    location.npcs = [npc_map[npc_id] for npc_id in unique_ids]


def location_query_options(stmt: Select[tuple[Location]]) -> Select[tuple[Location]]:
    return stmt.options(
        selectinload(Location.campaign),
        selectinload(Location.loot),
        selectinload(Location.objects),
        selectinload(Location.npcs),
        selectinload(Location.residents),
    )


def get_location_or_404(db: Session, location_id: int) -> Location:
    location = db.scalar(
        location_query_options(select(Location).where(Location.id == location_id))
    )
    if location is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Location not found.")
    return location


def apply_location_write(
    location: Location,
    *,
    title: str | None = None,
    description: str | None = None,
    player_visible: bool | None = None,
    partial: bool = False,
) -> None:
    if title is not None or not partial:
        cleaned = (title or "").strip() if title is not None else location.title
        if not cleaned:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Title is required.")
        location.title = cleaned
    if description is not None or not partial:
        location.description = description if description is not None else location.description
    if player_visible is not None or not partial:
        location.player_visible = bool(player_visible) if player_visible is not None else location.player_visible
