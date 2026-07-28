from fastapi import Depends, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.mappers import serialize_graph_detail, serialize_graph_list
from app.models import CharacterGraph, GraphEdge, GraphNode
from app.routers.graphs.shared import campaign_graphs_router, router
from app.schemas import GraphDetailRead, GraphWrite, GraphWritePartial, dump_graph_partial
from app.services.campaigns import get_campaign_or_404
from app.services.graphs import (
    ensure_default_relation_types,
    ensure_unique_graph_name,
    get_graph_or_404,
)
from app.services.pagination import paginate_select


@router.get("/graphs/{graph_id}/", response_model=GraphDetailRead)
def get_graph(graph_id: int, db: Session = Depends(get_db)):
    graph = get_graph_or_404(db, graph_id)
    return serialize_graph_detail(graph)


@router.patch("/graphs/{graph_id}/", response_model=GraphDetailRead)
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


@campaign_graphs_router.post("/", status_code=status.HTTP_201_CREATED, response_model=GraphDetailRead)
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
    # Seed relation types so webs created before the campaign-create seed still get defaults.
    ensure_default_relation_types(db, campaign_id)
    db.commit()
    graph = get_graph_or_404(db, graph.id)
    return serialize_graph_detail(graph)
