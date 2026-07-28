from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CampaignWrite(BaseModel):
    name: str = Field(max_length=200)


class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    image: str | None = None
    created_at: datetime
    updated_at: datetime


class CampaignListRead(CampaignRead):
    npc_count: int
