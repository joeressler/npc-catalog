from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import CharacterGraph, GraphEdge, GraphNode, RelationType
from app.schemas import (
    GraphEdgeWrite,
    GraphEdgeWritePartial,
    GraphNodePositionWrite,
    GraphNodeWrite,
    GraphWrite,
    GraphWritePartial,
    RelationTypeWrite,
    RelationTypeWritePartial,
    dump_graph_partial,
)
from app.serializers import (
    serialize_graph_detail,
    serialize_graph_edge,
    serialize_graph_list,
    serialize_graph_node,
    serialize_relation_type,
)
from app.services.graphs import (
    create_graph_edge,
    create_graph_node,
    ensure_default_relation_types,
    ensure_unique_graph_name,
    ensure_unique_relation_type_name,
    get_graph_edge_or_404,
    get_graph_node_or_404,
    get_graph_or_404,
    get_relation_type_or_404,
    validate_polarity,
)
from app.services.npcs import get_campaign_or_404
from app.services.pagination import paginate_select

router = APIRouter(tags=["graphs"])
campaign_graphs_router = APIRouter(prefix="/campaigns/{campaign_id}/graphs", tags=["graphs"])
campaign_relation_types_router = APIRouter(
    prefix="/campaigns/{campaign_id}/relation-types",
    tags=["relation-types"],
)
relation_types_router = APIRouter(tags=["relation-types"])
graph_nodes_router = APIRouter(tags=["graph-nodes"])
graph_edges_router = APIRouter(tags=["graph-edges"])


@router.get("/graphs/{graph_id}/")
def get_graph(graph_id: int, db: Session = Depends(get_db)):
    graph = get_graph_or_404(db, graph_id)
    return serialize_graph_detail(graph)


@router.patch("/graphs/{graph_id}/")
def update_graph(graph_id: int, payload: GraphWritePartial, db: Session = Depends(get_db)):
    graph = get_graph_or_404(db, graph_id)
    data = dump_graph_partial(payload)

    if "name" in data:
        ensure_unique_graph_name(
            db,
            campaign_id=graph.campaign_id,
            name=data["name"],
            exclude_graph_id=graph.id,
        )
        graph.name = data["name"].strip()
    if "notes" in data:
        graph.notes = data["notes"]

    db.commit()
    graph = get_graph_or_404(db, graph_id)
    return serialize_graph_detail(graph)


@router.delete("/graphs/{graph_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_graph(graph_id: int, db: Session = Depends(get_db)):
    graph = get_graph_or_404(db, graph_id)
    db.delete(graph)
    db.commit()


@campaign_graphs_router.get("/")
def list_campaign_graphs(
    campaign_id: int,
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    node_count = (
        select(func.count(GraphNode.id))
        .where(GraphNode.graph_id == CharacterGraph.id)
        .scalar_subquery()
    )
    edge_count = (
        select(func.count(GraphEdge.id))
        .where(GraphEdge.graph_id == CharacterGraph.id)
        .scalar_subquery()
    )
    stmt = (
        select(CharacterGraph, node_count.label("node_count"), edge_count.label("edge_count"))
        .where(CharacterGraph.campaign_id == campaign_id)
        .order_by(CharacterGraph.name.asc())
    )

    def serialize(row: tuple[CharacterGraph, int, int]) -> dict:
        graph, nodes, edges = row[0], row[1], row[2]
        return serialize_graph_list(graph, node_count=nodes, edge_count=edges).model_dump()

    return paginate_select(db, request, stmt, page, serialize)


@campaign_graphs_router.post("/", status_code=status.HTTP_201_CREATED)
def create_campaign_graph(
    campaign_id: int,
    payload: GraphWrite,
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    ensure_unique_graph_name(db, campaign_id=campaign_id, name=payload.name)

    graph = CharacterGraph(
        campaign_id=campaign_id,
        name=payload.name.strip(),
        notes=payload.notes.strip(),
    )
    db.add(graph)
    db.commit()
    graph = get_graph_or_404(db, graph.id)
    return serialize_graph_detail(graph)


@campaign_relation_types_router.get("/")
def list_campaign_relation_types(
    campaign_id: int,
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    ensure_default_relation_types(db, campaign_id)
    db.commit()

    stmt = (
        select(RelationType)
        .where(RelationType.campaign_id == campaign_id)
        .order_by(RelationType.name.asc())
    )

    def serialize(relation_type: RelationType) -> dict:
        return serialize_relation_type(relation_type).model_dump()

    return paginate_select(
        db,
        request,
        stmt,
        page,
        serialize,
        id_column=RelationType.id,
    )


@campaign_relation_types_router.post("/", status_code=status.HTTP_201_CREATED)
def create_campaign_relation_type(
    campaign_id: int,
    payload: RelationTypeWrite,
    db: Session = Depends(get_db),
):
    get_campaign_or_404(db, campaign_id)
    ensure_default_relation_types(db, campaign_id)
    ensure_unique_relation_type_name(db, campaign_id=campaign_id, name=payload.name)
    polarity = validate_polarity(payload.polarity)

    relation_type = RelationType(
        campaign_id=campaign_id,
        name=payload.name.strip(),
        polarity=polarity,
    )
    db.add(relation_type)
    db.commit()
    return serialize_relation_type(relation_type)


@relation_types_router.patch("/relation-types/{relation_type_id}/")
def update_relation_type(
    relation_type_id: int,
    payload: RelationTypeWritePartial,
    db: Session = Depends(get_db),
):
    relation_type = get_relation_type_or_404(db, relation_type_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"] is not None:
        ensure_unique_relation_type_name(
            db,
            campaign_id=relation_type.campaign_id,
            name=data["name"],
            exclude_relation_type_id=relation_type.id,
        )
        relation_type.name = data["name"].strip()
    if "polarity" in data and data["polarity"] is not None:
        relation_type.polarity = validate_polarity(data["polarity"])

    db.commit()
    return serialize_relation_type(relation_type)


@relation_types_router.delete("/relation-types/{relation_type_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_relation_type(relation_type_id: int, db: Session = Depends(get_db)):
    relation_type = get_relation_type_or_404(db, relation_type_id)
    in_use = db.scalar(
        select(GraphEdge.id).where(GraphEdge.relation_type_id == relation_type_id).limit(1)
    )
    if in_use is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a relation type that is used by graph edges.",
        )
    db.delete(relation_type)
    db.commit()


@router.post("/graphs/{graph_id}/nodes/", status_code=status.HTTP_201_CREATED)
def add_graph_node(
    graph_id: int,
    payload: GraphNodeWrite,
    db: Session = Depends(get_db),
):
    graph = get_graph_or_404(db, graph_id)
    node = create_graph_node(db, graph, kind=payload.kind, npc_id=payload.npc_id)
    db.commit()
    return serialize_graph_node(node)


@graph_nodes_router.patch("/graph-nodes/{node_id}/")
def update_graph_node_position(
    node_id: int,
    payload: GraphNodePositionWrite,
    db: Session = Depends(get_db),
):
    node = get_graph_node_or_404(db, node_id)
    node.pos_x = payload.pos_x
    node.pos_y = payload.pos_y
    db.commit()
    node = get_graph_node_or_404(db, node_id)
    return serialize_graph_node(node)


@graph_nodes_router.delete("/graph-nodes/{node_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_graph_node(node_id: int, db: Session = Depends(get_db)):
    node = get_graph_node_or_404(db, node_id)
    db.execute(
        delete(GraphEdge).where(
            GraphEdge.graph_id == node.graph_id,
            (
                ((GraphEdge.from_kind == node.kind) & (GraphEdge.from_npc_id == node.npc_id))
                | ((GraphEdge.to_kind == node.kind) & (GraphEdge.to_npc_id == node.npc_id))
            ),
        )
    )
    db.delete(node)
    db.commit()


@router.post("/graphs/{graph_id}/edges/", status_code=status.HTTP_201_CREATED)
def add_graph_edge(
    graph_id: int,
    payload: GraphEdgeWrite,
    db: Session = Depends(get_db),
):
    graph = get_graph_or_404(db, graph_id)
    edge = create_graph_edge(
        db,
        graph,
        relation_type_id=payload.relation_type_id,
        from_kind=payload.from_kind,
        from_npc_id=payload.from_npc_id,
        to_kind=payload.to_kind,
        to_npc_id=payload.to_npc_id,
        notes=payload.notes,
    )
    db.commit()
    graph = get_graph_or_404(db, graph_id)
    return serialize_graph_edge(graph, edge)


@graph_edges_router.patch("/graph-edges/{edge_id}/")
def update_graph_edge(
    edge_id: int,
    payload: GraphEdgeWritePartial,
    db: Session = Depends(get_db),
):
    edge = get_graph_edge_or_404(db, edge_id)
    graph = get_graph_or_404(db, edge.graph_id)
    data = payload.model_dump(exclude_unset=True)

    if "relation_type_id" in data and data["relation_type_id"] is not None:
        relation_type = get_relation_type_or_404(db, data["relation_type_id"])
        if relation_type.campaign_id != graph.campaign_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Relation type must belong to the graph's campaign.",
            )
        edge.relation_type_id = relation_type.id
    if "notes" in data and data["notes"] is not None:
        edge.notes = data["notes"].strip()

    db.commit()
    graph = get_graph_or_404(db, edge.graph_id)
    edge = get_graph_edge_or_404(db, edge_id)
    return serialize_graph_edge(graph, edge)


@graph_edges_router.delete("/graph-edges/{edge_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_graph_edge(edge_id: int, db: Session = Depends(get_db)):
    edge = get_graph_edge_or_404(db, edge_id)
    db.delete(edge)
    db.commit()
