import json
from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import ValidationError
from sqlalchemy import select

from app.constants import NPC_IMPORT_MAX_CHARACTERS
from app.deps import DbSession
from app.mappers import serialize_npc_detail, serialize_npc_list
from app.media import delete_npc_image, is_upload_file, save_npc_image
from app.models import NPC, Campaign
from app.player_access import ensure_campaign_visible, ensure_npc_visible, is_player
from app.schemas import (
    NPCDetailRead,
    NPCImportCreated,
    NPCImportFailed,
    NPCImportFieldError,
    NPCImportItem,
    NPCImportResult,
    NPCWrite,
    NPCWritePartial,
    dump_partial,
    format_import_field_errors,
)
from app.services.campaigns import get_campaign_or_404
from app.services.npcs import (
    apply_npc_filters,
    apply_npc_ordering,
    create_npc_from_write,
    get_npc_or_404,
    npc_location_id_error,
    npc_query_options,
    sync_aliases,
    sync_tags,
    validate_npc_location_id,
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
    elif is_upload_file(image_field):
        delete_npc_image(npc.image_path)
        npc.image_path = save_npc_image(image_field)


def _player_npc_stmt(stmt, *, for_player: bool):
    if not for_player:
        return stmt
    return stmt.join(NPC.campaign).where(
        NPC.player_visible.is_(True),
        Campaign.player_visible.is_(True),
    )


@router.get("/npcs/")
def list_npcs(
    request: Request,
    db: DbSession,
    page: int = 1,
    q: str | None = None,
    alignment: str | None = None,
    tag: str | None = None,
    campaign: int | None = None,
    location: str | None = None,
    faction: str | None = None,
    ordering: Annotated[str | None, Query()] = None,
):
    for_player = is_player(request)
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
    stmt = _player_npc_stmt(stmt, for_player=for_player)
    stmt = apply_npc_ordering(stmt, ordering)
    return paginate_select(
        db,
        request,
        stmt,
        page,
        lambda npc: serialize_npc_list(npc, request).model_dump(),
        id_column=NPC.id,
    )


@router.get("/npcs/{npc_id}/", response_model=NPCDetailRead)
def get_npc(npc_id: int, request: Request, db: DbSession):
    for_player = is_player(request)
    npc = get_npc_or_404(db, npc_id)
    ensure_npc_visible(npc, for_player=for_player)
    return serialize_npc_detail(npc, request, for_player=for_player)


@router.patch("/npcs/{npc_id}/", response_model=NPCDetailRead)
async def update_npc(npc_id: int, request: Request, db: DbSession):
    npc = get_npc_or_404(db, npc_id)
    form = await request.form()
    data = _parse_json_form_payload(form.get("payload"))
    payload = _parse_partial_payload(data)

    if payload.campaign is not None:
        get_campaign_or_404(db, payload.campaign)

    campaign_id = payload.campaign if payload.campaign is not None else npc.campaign_id
    if payload.location_id is not None or "location_id" in data:
        validate_npc_location_id(db, campaign_id=campaign_id, location_id=payload.location_id)

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
def delete_npc(npc_id: int, db: DbSession):
    npc = get_npc_or_404(db, npc_id)
    delete_npc_image(npc.image_path)
    db.delete(npc)
    db.commit()


@campaign_npcs_router.get("/")
def list_campaign_npcs(
    campaign_id: int,
    request: Request,
    db: DbSession,
    page: int = 1,
    q: str | None = None,
    alignment: str | None = None,
    tag: str | None = None,
    location: str | None = None,
    faction: str | None = None,
    ordering: Annotated[str | None, Query()] = None,
):
    for_player = is_player(request)
    campaign = get_campaign_or_404(db, campaign_id)
    ensure_campaign_visible(campaign, for_player=for_player)
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
    if for_player:
        stmt = stmt.where(NPC.player_visible.is_(True))
    stmt = apply_npc_ordering(stmt, ordering)
    return paginate_select(
        db,
        request,
        stmt,
        page,
        lambda npc: serialize_npc_list(npc, request).model_dump(),
        id_column=NPC.id,
    )


@campaign_npcs_router.post("/", status_code=status.HTTP_201_CREATED, response_model=NPCDetailRead)
async def create_campaign_npc(
    campaign_id: int,
    request: Request,
    payload: Annotated[str, Form()],
    db: DbSession,
    image: Annotated[UploadFile | None, File()] = None,
):
    get_campaign_or_404(db, campaign_id)
    data = _parse_json_form_payload(payload)
    data["campaign"] = campaign_id
    write_payload = _parse_write_payload(data)

    validate_npc_location_id(
        db,
        campaign_id=campaign_id,
        location_id=write_payload.location_id,
    )

    image_path = None
    if image and image.filename:
        image_path = save_npc_image(image)

    npc = create_npc_from_write(
        db,
        campaign_id=campaign_id,
        fields=write_payload.model_dump(exclude={"aliases", "tags", "campaign"}),
        aliases=write_payload.aliases,
        tags=write_payload.tags,
        image_path=image_path,
    )
    db.commit()
    npc = get_npc_or_404(db, npc.id)
    return serialize_npc_detail(npc, request)


def _peek_import_name(item: object) -> str | None:
    if isinstance(item, dict):
        name = item.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return None


def _character_failed(
    *,
    index: int,
    name: str | None,
    errors: list[NPCImportFieldError],
) -> NPCImportFailed:
    return NPCImportFailed(index=index, name=name, errors=errors)


@campaign_npcs_router.post("/import/", response_model=NPCImportResult)
async def import_campaign_npcs(
    campaign_id: int,
    request: Request,
    db: DbSession,
):
    get_campaign_or_404(db, campaign_id)
    raw = await request.body()
    if not raw.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Payload is required.")
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.") from exc

    if isinstance(body, list):
        items = body
    elif isinstance(body, dict):
        if "characters" not in body:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Payload must include a characters array.",
            )
        if not isinstance(body["characters"], list):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="characters must be a JSON array.",
            )
        items = body["characters"]
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Payload must be a JSON object with a characters array, or a JSON array of characters.",
        )

    if len(items) > NPC_IMPORT_MAX_CHARACTERS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Import is limited to {NPC_IMPORT_MAX_CHARACTERS} characters at a time.",
        )

    created: list[NPCImportCreated] = []
    failed: list[NPCImportFailed] = []

    for index, item in enumerate(items):
        name_hint = _peek_import_name(item)
        if not isinstance(item, dict):
            failed.append(
                _character_failed(
                    index=index,
                    name=name_hint,
                    errors=[
                        NPCImportFieldError(
                            field=None,
                            message="Character must be a JSON object.",
                        )
                    ],
                )
            )
            continue

        try:
            payload = NPCImportItem.model_validate(item)
        except ValidationError as exc:
            failed.append(
                _character_failed(
                    index=index,
                    name=name_hint,
                    errors=format_import_field_errors(exc.errors()),
                )
            )
            continue

        location_error = npc_location_id_error(
            db,
            campaign_id=campaign_id,
            location_id=payload.location_id,
        )
        if location_error:
            failed.append(
                _character_failed(
                    index=index,
                    name=payload.name,
                    errors=[NPCImportFieldError(field="location_id", message=location_error)],
                )
            )
            continue

        try:
            with db.begin_nested():
                npc = create_npc_from_write(
                    db,
                    campaign_id=campaign_id,
                    fields=payload.model_dump(exclude={"aliases", "tags"}),
                    aliases=payload.aliases,
                    tags=payload.tags,
                )
            created.append(NPCImportCreated(id=npc.id, name=npc.name, index=index))
        except Exception:
            failed.append(
                _character_failed(
                    index=index,
                    name=payload.name,
                    errors=[
                        NPCImportFieldError(
                            field=None,
                            message="Could not create this character.",
                        )
                    ],
                )
            )

    db.commit()
    return NPCImportResult(
        created_count=len(created),
        failed_count=len(failed),
        created=created,
        failed=failed,
    )
