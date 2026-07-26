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
    image: str | None = None
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


class SessionCharacterRead(BaseModel):
    id: int
    name: str
    role_occupation: str
    alignment: str
    alignment_display: str


class SessionListRead(BaseModel):
    id: int
    campaign: int
    number: int
    title: str
    character_count: int
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
    characters: list[SessionCharacterRead]
    created_at: datetime
    updated_at: datetime


class SessionWrite(BaseModel):
    number: int | None = None
    title: str = ""
    overall_notes: str = ""
    story_paths: list[SessionStoryPathWrite] = Field(default_factory=list)
    clues: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    character_ids: list[int] = Field(default_factory=list)


class SessionWritePartial(BaseModel):
    number: int | None = None
    title: str | None = None
    overall_notes: str | None = None
    story_paths: list[SessionStoryPathWrite] | None = None
    clues: list[str] | None = None
    secrets: list[str] | None = None
    character_ids: list[int] | None = None


def dump_session_partial(payload: SessionWritePartial) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True)


class RelationTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    polarity: str


class RelationTypeWrite(BaseModel):
    name: str = Field(max_length=100)
    polarity: str = Field(max_length=20)


class RelationTypeWritePartial(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    polarity: str | None = Field(default=None, max_length=20)


class GraphEndpointRead(BaseModel):
    node_id: int
    kind: str
    npc_id: int | None = None
    label: str


class GraphNodeRead(BaseModel):
    id: int
    kind: str
    npc_id: int | None = None
    label: str
    pos_x: float | None = None
    pos_y: float | None = None


class GraphNodeWrite(BaseModel):
    kind: str = Field(max_length=20)
    npc_id: int | None = None
    label: str | None = Field(default=None, max_length=200)


class GraphNodePositionWrite(BaseModel):
    pos_x: float
    pos_y: float


class GraphEdgeRead(BaseModel):
    id: int
    relation_type: RelationTypeRead
    from_endpoint: GraphEndpointRead
    to_endpoint: GraphEndpointRead
    notes: str


class GraphEdgeWrite(BaseModel):
    relation_type_id: int
    from_node_id: int
    to_node_id: int
    notes: str = ""
    bidirectional: bool = False


class GraphEdgeWritePartial(BaseModel):
    relation_type_id: int | None = None
    notes: str | None = None


class GraphListRead(BaseModel):
    id: int
    campaign: int
    name: str
    notes: str
    node_count: int
    edge_count: int
    created_at: datetime
    updated_at: datetime


class GraphDetailRead(BaseModel):
    id: int
    campaign: int
    name: str
    notes: str
    nodes: list[GraphNodeRead]
    edges: list[GraphEdgeRead]
    created_at: datetime
    updated_at: datetime


class GraphWrite(BaseModel):
    name: str = Field(max_length=200)
    notes: str = ""


class GraphWritePartial(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    notes: str | None = None


def dump_graph_partial(payload: GraphWritePartial) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True)
