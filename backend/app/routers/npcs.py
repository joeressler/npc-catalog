import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.media import delete_npc_image, save_npc_image
from app.models import NPC
from app.schemas import NPCWrite, NPCWritePartial, dump_partial
from app.serializers import serialize_npc_detail, serialize_npc_list
from app.services.npcs import (
    apply_npc_filters,
    apply_npc_ordering,
    get_campaign_or_404,
    get_npc_or_404,
    npc_query_options,
    sync_aliases,
    sync_tags,
)
from app.services.pagination import paginate_select

router = APIRouter(tags=["npcs"])
campaign_npcs_router = APIRouter(prefix="/campaigns/{campaign_id}/npcs", tags=["npcs"])


def _parse_write_payload(data: dict) -> NPCWrite:
    try:
        return NPCWrite.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.errors()) from exc


def _parse_partial_payload(data: dict) -> NPCWritePartial:
    try:
        return NPCWritePartial.model_validate(data)
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


def _apply_write_fields(npc: NPC, payload: NPCWrite | NPCWritePartial, *, partial: bool = False) -> None:
    if partial:
        data = dump_partial(payload)
        data.pop("aliases", None)
        data.pop("tags", None)
        for key, value in data.items():
            if key == "campaign":
                npc.campaign_id = value
            else:
                setattr(npc, key, value)
        return

    data = payload.model_dump(exclude={"aliases", "tags", "campaign"})
    for key, value in data.items():
        setattr(npc, key, value)


def _apply_image_from_form(npc: NPC, form) -> None:
    if "image" not in form:
        return
    image_field = form.get("image")
    if image_field == "" or (isinstance(image_field, str) and image_field == ""):
        delete_npc_image(npc.image_path)
        npc.image_path = None
    elif isinstance(image_field, UploadFile) and image_field.filename:
        delete_npc_image(npc.image_path)
        npc.image_path = save_npc_image(image_field)


@router.get("/npcs/")
def list_npcs(
    request: Request,
    page: int = 1,
    q: str | None = None,
    alignment: str | None = None,
    tag: str | None = None,
    campaign: int | None = None,
    location: str | None = None,
    faction: str | None = None,
    ordering: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = npc_query_options(select(NPC))
    stmt = apply_npc_filters(
        stmt,
        q=q,
        alignment=alignment,
        tag=tag,
        campaign_id=campaign,
        location=location,
        faction=faction,
    )
    stmt = apply_npc_ordering(stmt, ordering)
    return paginate_select(
        db,
        request,
        stmt,
        page,
        lambda npc: serialize_npc_list(npc, request).model_dump(),
        id_column=NPC.id,
    )


@router.get("/npcs/{npc_id}/")
def get_npc(npc_id: int, request: Request, db: Session = Depends(get_db)):
    npc = get_npc_or_404(db, npc_id)
    return serialize_npc_detail(npc, request)


@router.patch("/npcs/{npc_id}/")
async def update_npc(npc_id: int, request: Request, db: Session = Depends(get_db)):
    npc = get_npc_or_404(db, npc_id)
    form = await request.form()
    data = _parse_json_form_payload(form.get("payload"))
    payload = _parse_partial_payload(data)

    if payload.campaign is not None:
        get_campaign_or_404(db, payload.campaign)

    _apply_write_fields(npc, payload, partial=True)
    _apply_image_from_form(npc, form)

    if payload.aliases is not None:
        sync_aliases(db, npc, payload.aliases)
    if payload.tags is not None:
        sync_tags(db, npc, payload.tags)

    db.commit()
    npc = get_npc_or_404(db, npc_id)
    return serialize_npc_detail(npc, request)


@router.delete("/npcs/{npc_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_npc(npc_id: int, db: Session = Depends(get_db)):
    npc = get_npc_or_404(db, npc_id)
    delete_npc_image(npc.image_path)
    db.delete(npc)
    db.commit()


@campaign_npcs_router.get("/")
def list_campaign_npcs(
    campaign_id: int,
    request: Request,
    page: int = 1,
    q: str | None = None,
    alignment: str | None = None,
    tag: str | None = None,
    location: str | None = None,
    faction: str | None = None,
    ordering: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    stmt = npc_query_options(select(NPC))
    stmt = apply_npc_filters(
        stmt,
        q=q,
        alignment=alignment,
        tag=tag,
        campaign_id=campaign_id,
        location=location,
        faction=faction,
    )
    stmt = apply_npc_ordering(stmt, ordering)
    return paginate_select(
        db,
        request,
        stmt,
        page,
        lambda npc: serialize_npc_list(npc, request).model_dump(),
        id_column=NPC.id,
    )


@campaign_npcs_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_campaign_npc(
    campaign_id: int,
    request: Request,
    payload: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    data = _parse_json_form_payload(payload)
    data["campaign"] = campaign_id
    write_payload = _parse_write_payload(data)

    image_path = None
    if image and image.filename:
        image_path = save_npc_image(image)

    npc = NPC(campaign_id=campaign_id, image_path=image_path)
    _apply_write_fields(npc, write_payload)
    db.add(npc)
    db.flush()
    sync_aliases(db, npc, write_payload.aliases)
    sync_tags(db, npc, write_payload.tags)
    db.commit()
    npc = get_npc_or_404(db, npc.id)
    return serialize_npc_detail(npc, request)
