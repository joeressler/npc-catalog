from fastapi import APIRouter, Request, status
from sqlalchemy import func, select

from app.deps import DbSession
from app.mappers import serialize_encounter_detail, serialize_encounter_list
from app.models import Encounter, EncounterEnemy, EncounterNPC
from app.schemas import (
    EncounterDetailRead,
    EncounterWrite,
    EncounterWritePartial,
    dump_encounter_partial,
)
from app.services.campaigns import get_campaign_or_404
from app.services.encounters import (
    apply_encounter_write,
    clone_encounter,
    get_encounter_or_404,
    sync_enemies,
    sync_loot,
    sync_npcs,
    sync_objects,
)
from app.services.pagination import paginate_select

router = APIRouter(tags=["encounters"])
campaign_encounters_router = APIRouter(
    prefix="/campaigns/{campaign_id}/encounters",
    tags=["encounters"],
)


@router.get("/encounters/{encounter_id}/", response_model=EncounterDetailRead)
def get_encounter(encounter_id: int, db: DbSession):
    encounter = get_encounter_or_404(db, encounter_id)
    return serialize_encounter_detail(encounter)


@router.patch("/encounters/{encounter_id}/", response_model=EncounterDetailRead)
def update_encounter(
    encounter_id: int,
    payload: EncounterWritePartial,
    db: DbSession,
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
    if payload.npc_ids is not None:
        sync_npcs(db, encounter, payload.npc_ids)

    db.commit()
    encounter = get_encounter_or_404(db, encounter_id)
    return serialize_encounter_detail(encounter)


@router.delete("/encounters/{encounter_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_encounter(encounter_id: int, db: DbSession):
    encounter = get_encounter_or_404(db, encounter_id)
    db.delete(encounter)
    db.commit()


@router.post(
    "/encounters/{encounter_id}/clone/",
    status_code=status.HTTP_201_CREATED,
    response_model=EncounterDetailRead,
)
def clone_encounter_endpoint(encounter_id: int, db: DbSession):
    source = get_encounter_or_404(db, encounter_id)
    cloned = clone_encounter(db, source)
    db.commit()
    return serialize_encounter_detail(cloned)


@campaign_encounters_router.get("/")
def list_campaign_encounters(
    campaign_id: int,
    request: Request,
    db: DbSession,
    page: int = 1,
):
    get_campaign_or_404(db, campaign_id)
    enemy_count = (
        select(func.count(EncounterEnemy.id))
        .where(EncounterEnemy.encounter_id == Encounter.id)
        .scalar_subquery()
    )
    npc_count = (
        select(func.count(EncounterNPC.npc_id))
        .where(EncounterNPC.encounter_id == Encounter.id)
        .scalar_subquery()
    )
    stmt = (
        select(
            Encounter,
            enemy_count.label("enemy_count"),
            npc_count.label("npc_count"),
        )
        .where(Encounter.campaign_id == campaign_id)
        .order_by(Encounter.title.asc())
    )

    def serialize(row: tuple) -> dict:
        encounter, enemies, npcs = row[0], row[1], row[2]
        return serialize_encounter_list(
            encounter,
            enemy_count=enemies,
            npc_count=npcs,
        ).model_dump()

    return paginate_select(db, request, stmt, page, serialize)


@campaign_encounters_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=EncounterDetailRead,
)
def create_campaign_encounter(
    campaign_id: int,
    payload: EncounterWrite,
    db: DbSession,
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
    sync_npcs(db, encounter, payload.npc_ids)
    db.commit()
    encounter = get_encounter_or_404(db, encounter.id)
    return serialize_encounter_detail(encounter)
