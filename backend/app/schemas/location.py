from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LocationLootRead(BaseModel):
    id: int
    description: str
    sort_order: int


class LocationObjectRead(BaseModel):
    id: int
    name: str
    description: str
    sort_order: int


class LocationObjectWrite(BaseModel):
    name: str = Field(max_length=200)
    description: str = ""


class LocationNpcRead(BaseModel):
    id: int
    name: str
    role_occupation: str
    alignment: str
    alignment_display: str


class CatalogLocationRead(BaseModel):
    id: int
    title: str


class LocationListRead(BaseModel):
    id: int
    campaign: int
    title: str
    description: str
    image: str | None = None
    player_visible: bool = False
    npc_count: int
    created_at: datetime
    updated_at: datetime


class LocationDetailRead(BaseModel):
    id: int
    campaign: int
    title: str
    description: str
    image: str | None = None
    player_visible: bool = False
    loot: list[LocationLootRead]
    objects: list[LocationObjectRead]
    npcs: list[LocationNpcRead]
    residents: list[LocationNpcRead]
    created_at: datetime
    updated_at: datetime


class LocationWrite(BaseModel):
    title: str = Field(max_length=200)
    description: str = ""
    player_visible: bool = False
    loot: list[str] = Field(default_factory=list)
    objects: list[LocationObjectWrite] = Field(default_factory=list)
    npc_ids: list[int] = Field(default_factory=list)


class LocationWritePartial(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    player_visible: bool | None = None
    loot: list[str] | None = None
    objects: list[LocationObjectWrite] | None = None
    npc_ids: list[int] | None = None


def dump_location_partial(payload: LocationWritePartial) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True)
