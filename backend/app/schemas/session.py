from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionLineItemRead(BaseModel):
    id: int
    text: str
    sort_order: int


class SessionStoryPathRead(BaseModel):
    id: int
    name: str
    sort_order: int
    beats: list[SessionLineItemRead]


class SessionStoryPathWrite(BaseModel):
    name: str = Field(max_length=200)
    beats: list[str] = Field(default_factory=list)


class SessionNpcRead(BaseModel):
    id: int
    name: str
    role_occupation: str
    alignment: str
    alignment_display: str


class SessionEncounterRead(BaseModel):
    id: int
    title: str
    short_description: str


class SessionLocationRead(BaseModel):
    id: int
    title: str
    description: str


class SessionListRead(BaseModel):
    id: int
    campaign: int
    number: int
    title: str
    npc_count: int
    created_at: datetime
    updated_at: datetime


class SessionDetailRead(BaseModel):
    id: int
    campaign: int
    number: int
    title: str
    overall_notes: str
    story_paths: list[SessionStoryPathRead]
    clues: list[SessionLineItemRead]
    secrets: list[SessionLineItemRead]
    npcs: list[SessionNpcRead]
    encounters: list[SessionEncounterRead]
    locations: list[SessionLocationRead]
    created_at: datetime
    updated_at: datetime


class SessionWrite(BaseModel):
    number: int | None = None
    title: str = ""
    overall_notes: str = ""
    story_paths: list[SessionStoryPathWrite] = Field(default_factory=list)
    clues: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    npc_ids: list[int] = Field(default_factory=list)
    encounter_ids: list[int] = Field(default_factory=list)
    location_ids: list[int] = Field(default_factory=list)


class SessionWritePartial(BaseModel):
    number: int | None = None
    title: str | None = None
    overall_notes: str | None = None
    story_paths: list[SessionStoryPathWrite] | None = None
    clues: list[str] | None = None
    secrets: list[str] | None = None
    npc_ids: list[int] | None = None
    encounter_ids: list[int] | None = None
    location_ids: list[int] | None = None


def dump_session_partial(payload: SessionWritePartial) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True)
