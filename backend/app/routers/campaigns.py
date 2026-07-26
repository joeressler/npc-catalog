from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.media import delete_campaign_image, delete_npc_image, save_campaign_image
from app.models import Campaign, NPC
from app.serializers import serialize_campaign
from app.services.pagination import paginate_select

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/")
def list_campaigns(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
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


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_campaign(
    request: Request,
    name: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(Campaign).where(func.lower(Campaign.name) == name.strip().lower()))
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Campaign with this name already exists.")

    image_path = None
    if image and image.filename:
        image_path = save_campaign_image(image)

    campaign = Campaign(name=name.strip(), image_path=image_path)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return serialize_campaign(campaign, request)


@router.get("/{campaign_id}/")
def get_campaign(
    campaign_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return serialize_campaign(campaign, request)


@router.patch("/{campaign_id}/")
async def update_campaign(
    campaign_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    form = await request.form()
    name = form.get("name")
    if not name or not str(name).strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Name is required.")

    trimmed_name = str(name).strip()
    duplicate = db.scalar(
        select(Campaign).where(
            func.lower(Campaign.name) == trimmed_name.lower(),
            Campaign.id != campaign_id,
        )
    )
    if duplicate:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Campaign with this name already exists.")

    campaign.name = trimmed_name

    if "image" in form:
        image_field = form.get("image")
        if image_field == "" or (isinstance(image_field, str) and image_field == ""):
            delete_campaign_image(campaign.image_path)
            campaign.image_path = None
        elif isinstance(image_field, UploadFile) and image_field.filename:
            delete_campaign_image(campaign.image_path)
            campaign.image_path = save_campaign_image(image_field)

    db.commit()
    db.refresh(campaign)
    return serialize_campaign(campaign, request)


@router.delete("/{campaign_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    delete_campaign_image(campaign.image_path)
    for npc in campaign.npcs:
        delete_npc_image(npc.image_path)
    db.delete(campaign)
    db.commit()
