from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Encounter, EncounterEnemy, EncounterNPC
from app.schemas import EncounterWrite, EncounterWritePartial, dump_encounter_partial
from app.serializers import serialize_encounter_detail, serialize_encounter_list
from app.services.encounters import (
    apply_encounter_write,
    clone_encounter,
    get_encounter_or_404,
    sync_characters,
    sync_enemies,
    sync_loot,
    sync_objects,
)
from app.services.npcs import get_campaign_or_404
from app.services.pagination import paginate_select

router = APIRouter(tags=["encounters"])
campaign_encounters_router = APIRouter(
    prefix="/campaigns/{campaign_id}/encounters",
    tags=["encounters"],
)


@router.get("/encounters/{encounter_id}/")
def get_encounter(encounter_id: int, db: Session = Depends(get_db)):
    encounter = get_encounter_or_404(db, encounter_id)
    return serialize_encounter_detail(encounter)


@router.patch("/encounters/{encounter_id}/")
def update_encounter(
    encounter_id: int,
    payload: EncounterWritePartial,
    db: Session = Depends(get_db),
):
    encounter = get_encounter_or_404(db, encounter_id)
    data = dump_encounter_partial(payload)

    apply_encounter_write(
        encounter,
        title=data.get("title"),
        short_description=data.get("short_description"),
        battlefield_description=data.get("battlefield_description"),
        further_notes=data.get("further_notes"),
        partial=True,
    )

    if payload.enemies is not None:
        sync_enemies(db, encounter, payload.enemies)
    if payload.loot is not None:
        sync_loot(db, encounter, payload.loot)
    if payload.objects is not None:
        sync_objects(db, encounter, payload.objects)
    if payload.character_ids is not None:
        sync_characters(db, encounter, payload.character_ids)

    db.commit()
    encounter = get_encounter_or_404(db, encounter_id)
    return serialize_encounter_detail(encounter)


@router.delete("/encounters/{encounter_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_encounter(encounter_id: int, db: Session = Depends(get_db)):
    encounter = get_encounter_or_404(db, encounter_id)
    db.delete(encounter)
    db.commit()


@router.post("/encounters/{encounter_id}/clone/", status_code=status.HTTP_201_CREATED)
def clone_encounter_endpoint(encounter_id: int, db: Session = Depends(get_db)):
    source = get_encounter_or_404(db, encounter_id)
    cloned = clone_encounter(db, source)
    db.commit()
    return serialize_encounter_detail(cloned)


@campaign_encounters_router.get("/")
def list_campaign_encounters(
    campaign_id: int,
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    enemy_count = (
        select(func.count(EncounterEnemy.id))
        .where(EncounterEnemy.encounter_id == Encounter.id)
        .scalar_subquery()
    )
    character_count = (
        select(func.count(EncounterNPC.npc_id))
        .where(EncounterNPC.encounter_id == Encounter.id)
        .scalar_subquery()
    )
    stmt = (
        select(
            Encounter,
            enemy_count.label("enemy_count"),
            character_count.label("character_count"),
        )
        .where(Encounter.campaign_id == campaign_id)
        .order_by(Encounter.title.asc())
    )

    def serialize(row: tuple) -> dict:
        encounter, enemies, characters = row[0], row[1], row[2]
        return serialize_encounter_list(
            encounter,
            enemy_count=enemies,
            character_count=characters,
        ).model_dump()

    return paginate_select(db, request, stmt, page, serialize)


@campaign_encounters_router.post("/", status_code=status.HTTP_201_CREATED)
def create_campaign_encounter(
    campaign_id: int,
    payload: EncounterWrite,
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    encounter = Encounter(campaign_id=campaign_id, title="")
    apply_encounter_write(
        encounter,
        title=payload.title,
        short_description=payload.short_description,
        battlefield_description=payload.battlefield_description,
        further_notes=payload.further_notes,
        partial=False,
    )
    db.add(encounter)
    db.flush()
    sync_enemies(db, encounter, payload.enemies)
    sync_loot(db, encounter, payload.loot)
    sync_objects(db, encounter, payload.objects)
    sync_characters(db, encounter, payload.character_ids)
    db.commit()
    encounter = get_encounter_or_404(db, encounter.id)
    return serialize_encounter_detail(encounter)
