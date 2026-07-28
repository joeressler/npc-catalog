import json
from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import ValidationError
from sqlalchemy import func, or_, select

from app.deps import DbSession
from app.mappers import serialize_location_detail, serialize_location_list
from app.media import delete_location_image, save_location_image
from app.models import NPC, Location, LocationNPC
from app.schemas import LocationWrite, LocationWritePartial
from app.services.campaigns import get_campaign_or_404
from app.services.locations import (
    apply_location_write,
    get_location_or_404,
    sync_loot,
    sync_npcs,
    sync_objects,
)
from app.services.pagination import paginate_select

router = APIRouter(tags=["locations"])
campaign_locations_router = APIRouter(
    prefix="/campaigns/{campaign_id}/locations",
    tags=["locations"],
)


def _parse_write_payload(data: dict) -> LocationWrite:
    try:
        return LocationWrite.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.errors()) from exc


def _parse_partial_payload(data: dict) -> LocationWritePartial:
    try:
        return LocationWritePartial.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.errors()) from exc


def _parse_json_form_payload(raw: str | None) -> dict:
    if raw is None or not str(raw).strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Payload is required.")
    try:
        data = json.loads(str(raw))
    except json.JSONDecodeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.") from exc
    if not isinstance(data, dict):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Payload must be a JSON object.")
    return data


def _apply_image_from_form(location: Location, form) -> None:
    if "image" not in form:
        return
    image_field = form.get("image")
    if image_field == "" or (isinstance(image_field, str) and image_field == ""):
        delete_location_image(location.image_path)
        location.image_path = None
    elif isinstance(image_field, UploadFile) and image_field.filename:
        delete_location_image(location.image_path)
        location.image_path = save_location_image(image_field)


@router.get("/locations/{location_id}/")
def get_location(location_id: int, request: Request, db: DbSession):
    location = get_location_or_404(db, location_id)
    return serialize_location_detail(location, request)


@router.patch("/locations/{location_id}/")
async def update_location(location_id: int, request: Request, db: DbSession):
    location = get_location_or_404(db, location_id)
    form = await request.form()
    data = _parse_json_form_payload(form.get("payload"))
    payload = _parse_partial_payload(data)

    apply_location_write(
        location,
        title=data.get("title"),
        description=data.get("description"),
        partial=True,
    )

    if payload.loot is not None:
        sync_loot(db, location, payload.loot)
    if payload.objects is not None:
        sync_objects(db, location, payload.objects)
    if payload.npc_ids is not None:
        sync_npcs(db, location, payload.npc_ids)

    _apply_image_from_form(location, form)

    db.commit()
    location = get_location_or_404(db, location_id)
    return serialize_location_detail(location, request)


@router.delete("/locations/{location_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: DbSession):
    location = get_location_or_404(db, location_id)
    delete_location_image(location.image_path)
    db.delete(location)
    db.commit()


@campaign_locations_router.get("/")
def list_campaign_locations(
    campaign_id: int,
    request: Request,
    db: DbSession,
    page: int = 1,
):
    get_campaign_or_404(db, campaign_id)
    npc_count = (
        select(func.count(func.distinct(NPC.id)))
        .where(
            or_(
                NPC.location_id == Location.id,
                NPC.id.in_(
                    select(LocationNPC.npc_id).where(LocationNPC.location_id == Location.id)
                ),
            )
        )
        .correlate(Location)
        .scalar_subquery()
    )
    stmt = (
        select(Location, npc_count.label("npc_count"))
        .where(Location.campaign_id == campaign_id)
        .order_by(Location.title.asc())
    )

    def serialize(row: tuple) -> dict:
        location, count = row[0], row[1]
        return serialize_location_list(
            location,
            request,
            npc_count=count,
        ).model_dump()

    return paginate_select(db, request, stmt, page, serialize)


@campaign_locations_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_campaign_location(
    campaign_id: int,
    request: Request,
    payload: Annotated[str, Form()],
    db: DbSession,
    image: Annotated[UploadFile | None, File()] = None,
):
    get_campaign_or_404(db, campaign_id)
    data = _parse_json_form_payload(payload)
    write_payload = _parse_write_payload(data)

    image_path = None
    if image and image.filename:
        image_path = save_location_image(image)

    location = Location(campaign_id=campaign_id, title="", image_path=image_path)
    apply_location_write(
        location,
        title=write_payload.title,
        description=write_payload.description,
        partial=False,
    )
    db.add(location)
    db.flush()
    sync_loot(db, location, write_payload.loot)
    sync_objects(db, location, write_payload.objects)
    sync_npcs(db, location, write_payload.npc_ids)
    db.commit()
    location = get_location_or_404(db, location.id)
    return serialize_location_detail(location, request)
