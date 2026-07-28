from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EncounterEnemyRead(BaseModel):
    id: int
    quantity: int
    name: str
    creature_type: str
    sort_order: int


class EncounterEnemyWrite(BaseModel):
    quantity: int = Field(ge=1)
    name: str = Field(max_length=200)
    creature_type: str = Field(default="", max_length=200)


class EncounterLootRead(BaseModel):
    id: int
    description: str
    sort_order: int


class EncounterObjectRead(BaseModel):
    id: int
    name: str
    description: str
    sort_order: int


class EncounterObjectWrite(BaseModel):
    name: str = Field(max_length=200)
    description: str = ""


class EncounterNpcRead(BaseModel):
    id: int
    name: str
    role_occupation: str
    alignment: str
    alignment_display: str


class EncounterListRead(BaseModel):
    id: int
    campaign: int
    title: str
    short_description: str
    enemy_count: int
    npc_count: int
    created_at: datetime
    updated_at: datetime


class EncounterDetailRead(BaseModel):
    id: int
    campaign: int
    title: str
    short_description: str
    battlefield_description: str
    further_notes: str
    enemies: list[EncounterEnemyRead]
    loot: list[EncounterLootRead]
    objects: list[EncounterObjectRead]
    npcs: list[EncounterNpcRead]
    created_at: datetime
    updated_at: datetime


class EncounterWrite(BaseModel):
    title: str = Field(max_length=200)
    short_description: str = ""
    battlefield_description: str = ""
    further_notes: str = ""
    enemies: list[EncounterEnemyWrite] = Field(default_factory=list)
    loot: list[str] = Field(default_factory=list)
    objects: list[EncounterObjectWrite] = Field(default_factory=list)
    npc_ids: list[int] = Field(default_factory=list)


class EncounterWritePartial(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    short_description: str | None = None
    battlefield_description: str | None = None
    further_notes: str | None = None
    enemies: list[EncounterEnemyWrite] | None = None
    loot: list[str] | None = None
    objects: list[EncounterObjectWrite] | None = None
    npc_ids: list[int] | None = None


def dump_encounter_partial(payload: EncounterWritePartial) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True)
