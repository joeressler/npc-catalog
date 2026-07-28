from fastapi import APIRouter

router = APIRouter(tags=["graphs"])
campaign_graphs_router = APIRouter(prefix="/campaigns/{campaign_id}/graphs", tags=["graphs"])
campaign_relation_types_router = APIRouter(
    prefix="/campaigns/{campaign_id}/relation-types",
    tags=["relation-types"],
)
relation_types_router = APIRouter(tags=["relation-types"])
graph_nodes_router = APIRouter(tags=["graph-nodes"])
graph_edges_router = APIRouter(tags=["graph-edges"])
