from app.routers.graphs.shared import (
    campaign_graphs_router,
    campaign_relation_types_router,
    graph_edges_router,
    graph_nodes_router,
    relation_types_router,
    router,
)

# Import submodules for their side effect of registering routes on the shared routers.
from app.routers.graphs import edges, graphs_crud, nodes, relation_types  # noqa: E402,F401

__all__ = [
    "router",
    "campaign_graphs_router",
    "campaign_relation_types_router",
    "relation_types_router",
    "graph_nodes_router",
    "graph_edges_router",
]
