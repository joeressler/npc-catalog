from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile, status
from sqlalchemy import func, select

from app.deps import DbSession
from app.mappers import serialize_campaign
from app.media import save_campaign_image
from app.models import NPC, Campaign
from app.schemas import CampaignRead
from app.services.campaigns import (
    create_campaign as create_campaign_service,
)
from app.services.campaigns import (
    delete_campaign as delete_campaign_service,
)
from app.services.campaigns import (
    ensure_unique_campaign_name,
    get_campaign_or_404,
    update_campaign_fields,
)
from app.services.pagination import paginate_select

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/")
def list_campaigns(
    request: Request,
    db: DbSession,
    page: int = 1,
):
    npc_count = (
        select(func.count(NPC.id))
        .where(NPC.campaign_id == Campaign.id)
        .scalar_subquery()
    )
    stmt = select(Campaign, npc_count.label("npc_count")).order_by(Campaign.name.asc())

    def serialize(row: tuple[Campaign, int]) -> dict:
        campaign, count = row[0], row[1]
        return serialize_campaign(campaign, request, npc_count=count).model_dump()

    return paginate_select(db, request, stmt, page, serialize)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CampaignRead)
def create_campaign(
    request: Request,
    name: Annotated[str, Form()],
    db: DbSession,
    image: Annotated[UploadFile | None, File()] = None,
):
    ensure_unique_campaign_name(db, name=name)

    image_path = None
    if image and image.filename:
        image_path = save_campaign_image(image)

    campaign = create_campaign_service(db, name=name, image_path=image_path)
    return serialize_campaign(campaign, request)


@router.get("/{campaign_id}/", response_model=CampaignRead)
def get_campaign(
    campaign_id: int,
    request: Request,
    db: DbSession,
):
    campaign = get_campaign_or_404(db, campaign_id)
    return serialize_campaign(campaign, request)


@router.patch("/{campaign_id}/", response_model=CampaignRead)
async def update_campaign(
    campaign_id: int,
    request: Request,
    db: DbSession,
):
    campaign = get_campaign_or_404(db, campaign_id)

    form = await request.form()
    campaign = update_campaign_fields(
        db,
        campaign,
        name=form.get("name"),
        image_field=form.get("image"),
        image_provided="image" in form,
    )
    return serialize_campaign(campaign, request)


@router.delete("/{campaign_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: int, db: DbSession):
    campaign = get_campaign_or_404(db, campaign_id)
    delete_campaign_service(db, campaign)
