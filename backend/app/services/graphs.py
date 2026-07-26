from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.constants import (
    DEFAULT_RELATION_TYPES,
    PARTY_NODE_LABEL,
    RELATION_POLARITIES,
    VALID_NODE_KINDS,
)
from app.models import CharacterGraph, GraphEdge, GraphNode, NPC, RelationType


@dataclass(frozen=True)
class GraphEndpoint:
    kind: str
    npc_id: int | None


def ensure_default_relation_types(db: Session, campaign_id: int) -> None:
    for name, polarity in DEFAULT_RELATION_TYPES:
        existing = db.scalar(
            select(RelationType).where(
                RelationType.campaign_id == campaign_id,
                func.lower(RelationType.name) == name.lower(),
            )
        )
        if existing is None:
            db.add(RelationType(campaign_id=campaign_id, name=name, polarity=polarity))
    db.flush()


def graph_query_options(stmt: Select[tuple[CharacterGraph]]) -> Select[tuple[CharacterGraph]]:
    return stmt.options(
        selectinload(CharacterGraph.nodes).selectinload(GraphNode.npc),
        selectinload(CharacterGraph.edges).selectinload(GraphEdge.relation_type),
    )


def get_graph_or_404(db: Session, graph_id: int) -> CharacterGraph:
    graph = db.scalar(
        graph_query_options(select(CharacterGraph).where(CharacterGraph.id == graph_id))
    )
    if graph is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Graph not found.")
    return graph


def get_relation_type_or_404(db: Session, relation_type_id: int) -> RelationType:
    relation_type = db.get(RelationType, relation_type_id)
    if relation_type is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Relation type not found.")
    return relation_type


def get_graph_node_or_404(db: Session, node_id: int) -> GraphNode:
    node = db.scalar(
        select(GraphNode)
        .options(selectinload(GraphNode.npc), selectinload(GraphNode.graph))
        .where(GraphNode.id == node_id)
    )
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Graph node not found.")
    return node


def get_graph_edge_or_404(db: Session, edge_id: int) -> GraphEdge:
    edge = db.scalar(
        select(GraphEdge)
        .options(selectinload(GraphEdge.relation_type), selectinload(GraphEdge.graph))
        .where(GraphEdge.id == edge_id)
    )
    if edge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Graph edge not found.")
    return edge


def ensure_unique_graph_name(
    db: Session,
    *,
    campaign_id: int,
    name: str,
    exclude_graph_id: int | None = None,
) -> None:
    stmt = select(CharacterGraph).where(
        CharacterGraph.campaign_id == campaign_id,
        func.lower(CharacterGraph.name) == name.strip().lower(),
    )
    if exclude_graph_id is not None:
        stmt = stmt.where(CharacterGraph.id != exclude_graph_id)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="A graph with this name already exists in this campaign.",
        )


def ensure_unique_relation_type_name(
    db: Session,
    *,
    campaign_id: int,
    name: str,
    exclude_relation_type_id: int | None = None,
) -> None:
    stmt = select(RelationType).where(
        RelationType.campaign_id == campaign_id,
        func.lower(RelationType.name) == name.strip().lower(),
    )
    if exclude_relation_type_id is not None:
        stmt = stmt.where(RelationType.id != exclude_relation_type_id)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="A relation type with this name already exists in this campaign.",
        )


def validate_polarity(polarity: str) -> str:
    if polarity not in RELATION_POLARITIES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Polarity must be one of: {', '.join(sorted(RELATION_POLARITIES))}.",
        )
    return polarity


def validate_endpoint_kind(kind: str) -> str:
    if kind not in VALID_NODE_KINDS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Endpoint kind must be one of: {', '.join(sorted(VALID_NODE_KINDS))}.",
        )
    return kind


def validate_endpoint(endpoint: GraphEndpoint) -> GraphEndpoint:
    kind = validate_endpoint_kind(endpoint.kind)
    if kind == "party":
        if endpoint.npc_id is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Party endpoints must not include an NPC id.",
            )
        return GraphEndpoint(kind=kind, npc_id=None)
    if endpoint.npc_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="NPC endpoints must include an NPC id.",
        )
    return GraphEndpoint(kind=kind, npc_id=endpoint.npc_id)


def _node_matches_endpoint(node: GraphNode, endpoint: GraphEndpoint) -> bool:
    if node.kind != endpoint.kind:
        return False
    if endpoint.kind == "party":
        return node.npc_id is None
    return node.npc_id == endpoint.npc_id


def endpoint_exists_on_graph(graph: CharacterGraph, endpoint: GraphEndpoint) -> bool:
    return any(_node_matches_endpoint(node, endpoint) for node in graph.nodes)


def get_npc_for_graph(db: Session, graph: CharacterGraph, npc_id: int) -> NPC:
    npc = db.get(NPC, npc_id)
    if npc is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="NPC not found.")
    if npc.campaign_id != graph.campaign_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="NPC must belong to the graph's campaign.",
        )
    return npc


def create_graph_node(
    db: Session,
    graph: CharacterGraph,
    *,
    kind: str,
    npc_id: int | None = None,
) -> GraphNode:
    validated_kind = validate_endpoint_kind(kind)
    if validated_kind == "party":
        party_exists = db.scalar(
            select(GraphNode.id).where(
                GraphNode.graph_id == graph.id,
                GraphNode.kind == "party",
            )
        )
        if party_exists is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="This graph already has a Party node.",
            )
        node = GraphNode(graph_id=graph.id, kind="party", npc_id=None)
    else:
        if npc_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="NPC id is required.")
        get_npc_for_graph(db, graph, npc_id)
        duplicate = db.scalar(
            select(GraphNode.id).where(
                GraphNode.graph_id == graph.id,
                GraphNode.kind == "npc",
                GraphNode.npc_id == npc_id,
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="This NPC is already on the graph.",
            )
        node = GraphNode(graph_id=graph.id, kind="npc", npc_id=npc_id)

    db.add(node)
    db.flush()
    return db.scalar(
        select(GraphNode)
        .options(selectinload(GraphNode.npc))
        .where(GraphNode.id == node.id)
    )


def create_graph_edge(
    db: Session,
    graph: CharacterGraph,
    *,
    relation_type_id: int,
    from_kind: str,
    from_npc_id: int | None,
    to_kind: str,
    to_npc_id: int | None,
    notes: str = "",
) -> GraphEdge:
    from_endpoint = validate_endpoint(GraphEndpoint(kind=from_kind, npc_id=from_npc_id))
    to_endpoint = validate_endpoint(GraphEndpoint(kind=to_kind, npc_id=to_npc_id))

    if (
        from_endpoint.kind == "npc"
        and to_endpoint.kind == "npc"
        and from_endpoint.npc_id == to_endpoint.npc_id
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Self-loops are not allowed.")

    if not endpoint_exists_on_graph(graph, from_endpoint):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="From endpoint is not on this graph.",
        )
    if not endpoint_exists_on_graph(graph, to_endpoint):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="To endpoint is not on this graph.",
        )

    relation_type = get_relation_type_or_404(db, relation_type_id)
    if relation_type.campaign_id != graph.campaign_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Relation type must belong to the graph's campaign.",
        )

    if from_endpoint.kind == "npc" and from_endpoint.npc_id is not None:
        get_npc_for_graph(db, graph, from_endpoint.npc_id)
    if to_endpoint.kind == "npc" and to_endpoint.npc_id is not None:
        get_npc_for_graph(db, graph, to_endpoint.npc_id)

    duplicate = db.scalar(
        select(GraphEdge.id).where(
            GraphEdge.graph_id == graph.id,
            GraphEdge.from_kind == from_endpoint.kind,
            GraphEdge.from_npc_id == from_endpoint.npc_id,
            GraphEdge.to_kind == to_endpoint.kind,
            GraphEdge.to_npc_id == to_endpoint.npc_id,
            GraphEdge.relation_type_id == relation_type_id,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="This directed relation already exists on the graph.",
        )

    edge = GraphEdge(
        graph_id=graph.id,
        relation_type_id=relation_type_id,
        from_kind=from_endpoint.kind,
        from_npc_id=from_endpoint.npc_id,
        to_kind=to_endpoint.kind,
        to_npc_id=to_endpoint.npc_id,
        notes=notes.strip(),
    )
    db.add(edge)
    db.flush()
    return db.scalar(
        select(GraphEdge)
        .options(selectinload(GraphEdge.relation_type))
        .where(GraphEdge.id == edge.id)
    )


def node_label(node: GraphNode) -> str:
    if node.kind == "party":
        return PARTY_NODE_LABEL
    if node.npc is not None:
        return node.npc.name
    return "Unknown"
