from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
