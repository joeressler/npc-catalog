from fastapi import HTTPException, status
from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Encounter,
    EncounterEnemy,
    EncounterLoot,
    EncounterObject,
    NPC,
)
from app.schemas import EncounterEnemyWrite, EncounterObjectWrite


def _clean_line_items(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item.strip()]


def sync_enemies(db: Session, encounter: Encounter, enemies: list[EncounterEnemyWrite]) -> None:
    db.execute(delete(EncounterEnemy).where(EncounterEnemy.encounter_id == encounter.id))
    for sort_order, enemy in enumerate(enemies):
        name = enemy.name.strip()
        if not name:
            continue
        db.add(
            EncounterEnemy(
                encounter_id=encounter.id,
                quantity=enemy.quantity,
                name=name,
                creature_type=enemy.creature_type.strip(),
                sort_order=sort_order,
            )
        )


def sync_loot(db: Session, encounter: Encounter, texts: list[str]) -> None:
    db.execute(delete(EncounterLoot).where(EncounterLoot.encounter_id == encounter.id))
    for sort_order, text in enumerate(_clean_line_items(texts)):
        db.add(EncounterLoot(encounter_id=encounter.id, description=text, sort_order=sort_order))


def sync_objects(db: Session, encounter: Encounter, objects: list[EncounterObjectWrite]) -> None:
    db.execute(delete(EncounterObject).where(EncounterObject.encounter_id == encounter.id))
    for sort_order, obj in enumerate(objects):
        name = obj.name.strip()
        if not name:
            continue
        db.add(
            EncounterObject(
                encounter_id=encounter.id,
                name=name,
                description=obj.description.strip() if obj.description else "",
                sort_order=sort_order,
            )
        )


def sync_characters(db: Session, encounter: Encounter, character_ids: list[int]) -> None:
    if not character_ids:
        encounter.characters = []
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
        if npc.campaign_id != encounter.campaign_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Characters must belong to the encounter's campaign.",
            )

    encounter.characters = [npc_map[character_id] for character_id in unique_ids]


def encounter_query_options(stmt: Select[tuple[Encounter]]) -> Select[tuple[Encounter]]:
    return stmt.options(
        selectinload(Encounter.enemies),
        selectinload(Encounter.loot),
        selectinload(Encounter.objects),
        selectinload(Encounter.characters),
    )


def get_encounter_or_404(db: Session, encounter_id: int) -> Encounter:
    encounter = db.scalar(
        encounter_query_options(select(Encounter).where(Encounter.id == encounter_id))
    )
    if encounter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Encounter not found.")
    return encounter


def apply_encounter_write(
    encounter: Encounter,
    *,
    title: str | None = None,
    short_description: str | None = None,
    battlefield_description: str | None = None,
    further_notes: str | None = None,
    partial: bool = False,
) -> None:
    if title is not None or not partial:
        cleaned = (title or "").strip() if title is not None else encounter.title
        if not cleaned:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Title is required.")
        encounter.title = cleaned
    if short_description is not None or not partial:
        encounter.short_description = (
            short_description if short_description is not None else encounter.short_description
        )
    if battlefield_description is not None or not partial:
        encounter.battlefield_description = (
            battlefield_description
            if battlefield_description is not None
            else encounter.battlefield_description
        )
    if further_notes is not None or not partial:
        encounter.further_notes = (
            further_notes if further_notes is not None else encounter.further_notes
        )


def clone_encounter(db: Session, source: Encounter) -> Encounter:
    clone = Encounter(
        campaign_id=source.campaign_id,
        title=f"{source.title} (copy)",
        short_description=source.short_description,
        battlefield_description=source.battlefield_description,
        further_notes=source.further_notes,
    )
    db.add(clone)
    db.flush()

    for enemy in source.enemies:
        db.add(
            EncounterEnemy(
                encounter_id=clone.id,
                quantity=enemy.quantity,
                name=enemy.name,
                creature_type=enemy.creature_type,
                sort_order=enemy.sort_order,
            )
        )
    for loot in source.loot:
        db.add(
            EncounterLoot(
                encounter_id=clone.id,
                description=loot.description,
                sort_order=loot.sort_order,
            )
        )
    for obj in source.objects:
        db.add(
            EncounterObject(
                encounter_id=clone.id,
                name=obj.name,
                description=obj.description,
                sort_order=obj.sort_order,
            )
        )
    clone.characters = list(source.characters)
    db.flush()
    return get_encounter_or_404(db, clone.id)
