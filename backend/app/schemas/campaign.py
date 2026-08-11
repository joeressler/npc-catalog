from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CampaignWrite(BaseModel):
    name: str = Field(max_length=200)
    player_visible: bool = False


class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    image: str | None = None
    player_visible: bool = False
    created_at: datetime
    updated_at: datetime


class CampaignListRead(CampaignRead):
    npc_count: int
