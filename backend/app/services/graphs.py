from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.constants import (
    DEFAULT_RELATION_TYPES,
    PARTY_NODE_LABEL,
    RELATION_POLARITIES,
    VALID_NODE_KINDS,
)
from app.models import NPC, CharacterGraph, GraphEdge, GraphNode, RelationType


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
        selectinload(CharacterGraph.edges).selectinload(GraphEdge.from_node).selectinload(GraphNode.npc),
        selectinload(CharacterGraph.edges).selectinload(GraphEdge.to_node).selectinload(GraphNode.npc),
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
        .options(
            selectinload(GraphEdge.relation_type),
            selectinload(GraphEdge.graph),
            selectinload(GraphEdge.from_node).selectinload(GraphNode.npc),
            selectinload(GraphEdge.to_node).selectinload(GraphNode.npc),
        )
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


def find_party_node(db: Session, graph_id: int) -> GraphNode | None:
    return db.scalar(
        select(GraphNode).where(
            GraphNode.graph_id == graph_id,
            GraphNode.kind == "party",
        )
    )


def _count_pcs(db: Session, graph_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(GraphNode).where(
            GraphNode.graph_id == graph_id,
            GraphNode.kind == "pc",
        )
    ) or 0


def get_node_on_graph(db: Session, graph: CharacterGraph, node_id: int) -> GraphNode:
    node = db.get(GraphNode, node_id)
    if node is None or node.graph_id != graph.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Node must belong to this graph.",
        )
    return node


def create_graph_node(
    db: Session,
    graph: CharacterGraph,
    *,
    kind: str,
    npc_id: int | None = None,
    label: str | None = None,
) -> GraphNode:
    validated_kind = validate_endpoint_kind(kind)

    if validated_kind == "party":
        if find_party_node(db, graph.id) is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="This graph already has a Party node.",
            )
        node = GraphNode(graph_id=graph.id, kind="party", npc_id=None, label=None)

    elif validated_kind == "pc":
        name = (label or "").strip()
        if not name:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Player character name is required.",
            )
        if find_party_node(db, graph.id) is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Add the Party node before adding player characters.",
            )
        duplicate = db.scalar(
            select(GraphNode.id).where(
                GraphNode.graph_id == graph.id,
                GraphNode.kind == "pc",
                func.lower(GraphNode.label) == name.lower(),
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="A player character with this name is already on the graph.",
            )
        node = GraphNode(graph_id=graph.id, kind="pc", npc_id=None, label=name)
        # Child positions are relative to the Party compound parent in the UI.
        node.pos_x = 70.0
        node.pos_y = 40.0 + (36.0 * _count_pcs(db, graph.id))

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
        node = GraphNode(graph_id=graph.id, kind="npc", npc_id=npc_id, label=None)

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
    from_node_id: int,
    to_node_id: int,
    notes: str = "",
    skip_if_exists: bool = False,
) -> GraphEdge | None:
    from_node = get_node_on_graph(db, graph, from_node_id)
    to_node = get_node_on_graph(db, graph, to_node_id)

    if from_node.id == to_node.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Self-loops are not allowed.")

    relation_type = get_relation_type_or_404(db, relation_type_id)
    if relation_type.campaign_id != graph.campaign_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Relation type must belong to the graph's campaign.",
        )

    duplicate = db.scalar(
        select(GraphEdge.id).where(
            GraphEdge.graph_id == graph.id,
            GraphEdge.from_node_id == from_node.id,
            GraphEdge.to_node_id == to_node.id,
            GraphEdge.relation_type_id == relation_type_id,
        )
    )
    if duplicate is not None:
        if skip_if_exists:
            return None
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="This directed relation already exists on the graph.",
        )

    edge = GraphEdge(
        graph_id=graph.id,
        relation_type_id=relation_type_id,
        from_node_id=from_node.id,
        to_node_id=to_node.id,
        notes=notes.strip(),
    )
    db.add(edge)
    db.flush()
    return db.scalar(
        select(GraphEdge)
        .options(
            selectinload(GraphEdge.relation_type),
            selectinload(GraphEdge.from_node).selectinload(GraphNode.npc),
            selectinload(GraphEdge.to_node).selectinload(GraphNode.npc),
        )
        .where(GraphEdge.id == edge.id)
    )


def node_label(node: GraphNode) -> str:
    if node.kind == "party":
        return PARTY_NODE_LABEL
    if node.kind == "pc":
        return node.label or "Player"
    if node.npc is not None:
        return node.npc.name
    return "Unknown"


def delete_graph_node_and_dependents(db: Session, node: GraphNode) -> None:
    """Remove a node, its incident edges, and PC children when deleting Party."""
    from sqlalchemy import delete

    node_ids = [node.id]
    if node.kind == "party":
        pc_ids = db.scalars(
            select(GraphNode.id).where(
                GraphNode.graph_id == node.graph_id,
                GraphNode.kind == "pc",
            )
        ).all()
        node_ids.extend(pc_ids)

    db.execute(
        delete(GraphEdge).where(
            GraphEdge.graph_id == node.graph_id,
            (GraphEdge.from_node_id.in_(node_ids)) | (GraphEdge.to_node_id.in_(node_ids)),
        )
    )
    db.execute(delete(GraphNode).where(GraphNode.id.in_(node_ids)))
