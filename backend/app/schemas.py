from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import VALID_ALIGNMENTS


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AliasRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


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


class NPCWrite(BaseModel):
    campaign: int | None = None
    name: str = Field(max_length=200)
    role_occupation: str = Field(max_length=200)
    alignment: str = Field(max_length=2)
    location: str = Field(max_length=200)
    faction: str = ""
    attitude: str = Field(max_length=200)
    party_relationship: str = Field(max_length=200)
    appearance: str = ""
    voice_mannerisms: str = ""
    personality_traits: str = ""
    motivation_goal: str = ""
    secret_hook: str = ""
    knowledge: str = ""
    inventory: str = ""
    dm_notes: str = ""
    session_log: str = ""
    aliases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("alignment")
    @classmethod
    def validate_alignment(cls, value: str) -> str:
        if value not in VALID_ALIGNMENTS:
            raise ValueError("Invalid alignment code.")
        return value


class NPCWritePartial(BaseModel):
    campaign: int | None = None
    name: str | None = Field(default=None, max_length=200)
    role_occupation: str | None = Field(default=None, max_length=200)
    alignment: str | None = Field(default=None, max_length=2)
    location: str | None = Field(default=None, max_length=200)
    faction: str | None = None
    attitude: str | None = Field(default=None, max_length=200)
    party_relationship: str | None = Field(default=None, max_length=200)
    appearance: str | None = None
    voice_mannerisms: str | None = None
    personality_traits: str | None = None
    motivation_goal: str | None = None
    secret_hook: str | None = None
    knowledge: str | None = None
    inventory: str | None = None
    dm_notes: str | None = None
    session_log: str | None = None
    aliases: list[str] | None = None
    tags: list[str] | None = None

    @field_validator("alignment")
    @classmethod
    def validate_alignment(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_ALIGNMENTS:
            raise ValueError("Invalid alignment code.")
        return value


class NPCListRead(BaseModel):
    id: int
    campaign: int
    name: str
    role_occupation: str
    alignment: str
    alignment_display: str
    location: str
    faction: str
    attitude: str
    party_relationship: str
    aliases: list[AliasRead]
    tags: list[TagRead]
    created_at: datetime
    updated_at: datetime


class NPCDetailRead(NPCListRead):
    appearance: str
    voice_mannerisms: str
    personality_traits: str
    motivation_goal: str
    secret_hook: str
    knowledge: str
    inventory: str
    dm_notes: str
    session_log: str


def dump_partial(payload: NPCWritePartial) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True)
