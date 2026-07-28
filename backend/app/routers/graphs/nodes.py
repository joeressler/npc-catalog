from fastapi import status

from app.deps import DbSession
from app.mappers import serialize_graph_node
from app.routers.graphs.shared import graph_nodes_router, router
from app.schemas import GraphNodePositionWrite, GraphNodeRead, GraphNodeWrite
from app.services.graphs import (
    create_graph_node,
    delete_graph_node_and_dependents,
    get_graph_node_or_404,
    get_graph_or_404,
)


@router.post("/graphs/{graph_id}/nodes/", status_code=status.HTTP_201_CREATED, response_model=GraphNodeRead)
def add_graph_node(
    graph_id: int,
    payload: GraphNodeWrite,
    db: DbSession,
):
    graph = get_graph_or_404(db, graph_id)
    node = create_graph_node(
        db,
        graph,
        kind=payload.kind,
        npc_id=payload.npc_id,
        label=payload.label,
    )
    db.commit()
    return serialize_graph_node(node)


@graph_nodes_router.patch("/graph-nodes/{node_id}/", response_model=GraphNodeRead)
def update_graph_node_position(
    node_id: int,
    payload: GraphNodePositionWrite,
    db: DbSession,
):
    node = get_graph_node_or_404(db, node_id)
    node.pos_x = payload.pos_x
    node.pos_y = payload.pos_y
    db.commit()
    node = get_graph_node_or_404(db, node_id)
    return serialize_graph_node(node)


@graph_nodes_router.delete("/graph-nodes/{node_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_graph_node(node_id: int, db: DbSession):
    node = get_graph_node_or_404(db, node_id)
    delete_graph_node_and_dependents(db, node)
    db.commit()
