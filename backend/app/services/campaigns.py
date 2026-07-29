from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.media import (
    delete_campaign_image,
    delete_location_image,
    delete_npc_image,
    is_upload_file,
    save_campaign_image,
)
from app.models import Campaign
from app.services.graphs import ensure_default_relation_types


def get_campaign_or_404(db: Session, campaign_id: int) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return campaign


def ensure_unique_campaign_name(
    db: Session,
    *,
    name: str,
    exclude_campaign_id: int | None = None,
) -> str:
    trimmed = name.strip()
    stmt = select(Campaign).where(func.lower(Campaign.name) == trimmed.lower())
    if exclude_campaign_id is not None:
        stmt = stmt.where(Campaign.id != exclude_campaign_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Campaign with this name already exists.",
        )
    return trimmed


def create_campaign(db: Session, *, name: str, image_path: str | None) -> Campaign:
    trimmed = ensure_unique_campaign_name(db, name=name)

    campaign = Campaign(name=trimmed, image_path=image_path)
    db.add(campaign)
    db.flush()
    ensure_default_relation_types(db, campaign.id)
    db.commit()
    db.refresh(campaign)
    return campaign


def update_campaign_fields(
    db: Session,
    campaign: Campaign,
    *,
    name: str | None,
    image_field: object,
    image_provided: bool,
) -> Campaign:
    if not name or not str(name).strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Name is required.")

    campaign.name = ensure_unique_campaign_name(
        db,
        name=str(name),
        exclude_campaign_id=campaign.id,
    )

    if image_provided:
        if isinstance(image_field, str) and image_field == "":
            delete_campaign_image(campaign.image_path)
            campaign.image_path = None
        elif is_upload_file(image_field):
            delete_campaign_image(campaign.image_path)
            campaign.image_path = save_campaign_image(image_field)

    db.commit()
    db.refresh(campaign)
    return campaign


def delete_campaign(db: Session, campaign: Campaign) -> None:
    delete_campaign_image(campaign.image_path)
    for npc in campaign.npcs:
        delete_npc_image(npc.image_path)
    for location in campaign.locations:
        delete_location_image(location.image_path)
    db.delete(campaign)
    db.commit()
