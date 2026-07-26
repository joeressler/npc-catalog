from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Alias, Campaign, NPC, NPCTag, Tag


def _clean_alias_names(alias_names: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for name in alias_names:
        trimmed = name.strip()
        if trimmed and trimmed.lower() not in seen:
            seen.add(trimmed.lower())
            cleaned.append(trimmed)
    return cleaned


def sync_aliases(db: Session, npc: NPC, alias_names: list[str]) -> None:
    db.execute(delete(Alias).where(Alias.npc_id == npc.id))
    for name in _clean_alias_names(alias_names):
        db.add(Alias(npc_id=npc.id, name=name))


def sync_tags(db: Session, npc: NPC, tag_names: list[str]) -> None:
    tag_objects: list[Tag] = []
    for name in tag_names:
        trimmed = name.strip()
        if not trimmed:
            continue
        tag = db.scalar(select(Tag).where(func.lower(Tag.name) == trimmed.lower()))
        if tag is None:
            tag = Tag(name=trimmed)
            db.add(tag)
            db.flush()
        tag_objects.append(tag)
    npc.tags = tag_objects


def npc_query_options(stmt: Select[tuple[NPC]]) -> Select[tuple[NPC]]:
    return stmt.options(
        joinedload(NPC.campaign),
        selectinload(NPC.aliases),
        selectinload(NPC.tags),
    )


def apply_npc_filters(
    stmt: Select[tuple[NPC]],
    *,
    q: str | None = None,
    alignment: str | None = None,
    tag: str | None = None,
    campaign_id: int | None = None,
    location: str | None = None,
    faction: str | None = None,
) -> Select[tuple[NPC]]:
    if campaign_id is not None:
        stmt = stmt.where(NPC.campaign_id == campaign_id)
    if alignment:
        stmt = stmt.where(NPC.alignment == alignment)
    if location:
        stmt = stmt.where(NPC.location.ilike(f"%{location}%"))
    if faction:
        stmt = stmt.where(NPC.faction.ilike(f"%{faction}%"))
    if tag:
        stmt = stmt.join(NPC.tags).where(func.lower(Tag.name) == tag.lower()).distinct()
    if q:
        search = f"%{q}%"
        alias_match = select(Alias.id).where(
            Alias.npc_id == NPC.id,
            Alias.name.ilike(search),
        ).exists()
        tag_match = select(NPCTag.npc_id).join(Tag).where(
            NPCTag.npc_id == NPC.id,
            Tag.name.ilike(search),
        ).exists()
        stmt = stmt.where(
            or_(
                NPC.name.ilike(search),
                NPC.role_occupation.ilike(search),
                alias_match,
                tag_match,
            )
        ).distinct()
    return stmt


def apply_npc_ordering(stmt: Select[tuple[NPC]], ordering: str | None) -> Select[tuple[NPC]]:
    field = ordering or "name"
    descending = field.startswith("-")
    key = field.lstrip("-")
    column_map = {
        "name": NPC.name,
        "updated_at": NPC.updated_at,
        "created_at": NPC.created_at,
    }
    column = column_map.get(key, NPC.name)
    return stmt.order_by(column.desc() if descending else column.asc())


def get_campaign_or_404(db: Session, campaign_id: int) -> Campaign:
    from fastapi import HTTPException, status

    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return campaign


def get_npc_or_404(db: Session, npc_id: int) -> NPC:
    from fastapi import HTTPException, status

    npc = db.scalar(npc_query_options(select(NPC).where(NPC.id == npc_id)))
    if npc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NPC not found.")
    return npc
