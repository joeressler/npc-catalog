from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.mappers import serialize_graph_edge
from app.routers.graphs.shared import graph_edges_router, router
from app.schemas import GraphEdgeRead, GraphEdgeWrite, GraphEdgeWritePartial
from app.services.graphs import (
    create_graph_edge,
    get_graph_edge_or_404,
    get_graph_or_404,
    get_relation_type_or_404,
)


@router.post("/graphs/{graph_id}/edges/", status_code=status.HTTP_201_CREATED, response_model=GraphEdgeRead)
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
        from_node_id=payload.from_node_id,
        to_node_id=payload.to_node_id,
        notes=payload.notes,
    )
    assert edge is not None
    if payload.bidirectional:
        create_graph_edge(
            db,
            graph,
            relation_type_id=payload.relation_type_id,
            from_node_id=payload.to_node_id,
            to_node_id=payload.from_node_id,
            notes=payload.notes,
            skip_if_exists=True,
        )
    db.commit()
    return serialize_graph_edge(edge)


@graph_edges_router.patch("/graph-edges/{edge_id}/", response_model=GraphEdgeRead)
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
    edge = get_graph_edge_or_404(db, edge_id)
    return serialize_graph_edge(edge)


@graph_edges_router.delete("/graph-edges/{edge_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_graph_edge(edge_id: int, db: Session = Depends(get_db)):
    edge = get_graph_edge_or_404(db, edge_id)
    db.delete(edge)
    db.commit()
