from fastapi import Request

from app.constants import ALIGNMENT_DISPLAY
from app.media import build_media_url
from app.models import Campaign, CharacterGraph, GameSession, GraphEdge, GraphNode, NPC
from app.schemas import (
    AliasRead,
    CampaignListRead,
    CampaignRead,
    GraphDetailRead,
    GraphEdgeRead,
    GraphEndpointRead,
    GraphListRead,
    GraphNodeRead,
    NPCDetailRead,
    NPCListRead,
    RelationTypeRead,
    SessionCharacterRead,
    SessionDetailRead,
    SessionLineItemRead,
    SessionListRead,
    SessionStoryPathRead,
    TagRead,
)
from app.services.graphs import node_label


def serialize_campaign(campaign: Campaign, request: Request, *, npc_count: int | None = None) -> CampaignRead | CampaignListRead:
    base_url = str(request.base_url)
    image = build_media_url(base_url, campaign.image_path)
    data = {
        "id": campaign.id,
        "name": campaign.name,
        "image": image,
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
    }
    if npc_count is not None:
        return CampaignListRead(**data, npc_count=npc_count)
    return CampaignRead(**data)


def serialize_npc_list(npc: NPC) -> NPCListRead:
    return NPCListRead(
        id=npc.id,
        campaign=npc.campaign_id,
        name=npc.name,
        role_occupation=npc.role_occupation,
        alignment=npc.alignment,
        alignment_display=ALIGNMENT_DISPLAY[npc.alignment],
        location=npc.location,
        faction=npc.faction,
        attitude=npc.attitude,
        party_relationship=npc.party_relationship,
        aliases=[AliasRead.model_validate(alias) for alias in npc.aliases],
        tags=[TagRead.model_validate(tag) for tag in npc.tags],
        created_at=npc.created_at,
        updated_at=npc.updated_at,
    )


def serialize_npc_detail(npc: NPC) -> NPCDetailRead:
    base = serialize_npc_list(npc)
    return NPCDetailRead(
        **base.model_dump(),
        appearance=npc.appearance,
        voice_mannerisms=npc.voice_mannerisms,
        personality_traits=npc.personality_traits,
        motivation_goal=npc.motivation_goal,
        secret_hook=npc.secret_hook,
        knowledge=npc.knowledge,
        inventory=npc.inventory,
        dm_notes=npc.dm_notes,
        session_log=npc.session_log,
    )


def serialize_session_list(session: GameSession, *, character_count: int | None = None) -> SessionListRead:
    count = character_count if character_count is not None else len(session.characters)
    return SessionListRead(
        id=session.id,
        campaign=session.campaign_id,
        number=session.number,
        title=session.title,
        character_count=count,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def serialize_session_detail(session: GameSession) -> SessionDetailRead:
    return SessionDetailRead(
        id=session.id,
        campaign=session.campaign_id,
        number=session.number,
        title=session.title,
        overall_notes=session.overall_notes,
        story_paths=[
            SessionStoryPathRead(
                id=path.id,
                name=path.name,
                sort_order=path.sort_order,
                beats=[
                    SessionLineItemRead(id=beat.id, text=beat.text, sort_order=beat.sort_order)
                    for beat in path.beats
                ],
            )
            for path in session.story_paths
        ],
        clues=[
            SessionLineItemRead(id=clue.id, text=clue.text, sort_order=clue.sort_order)
            for clue in session.clues
        ],
        secrets=[
            SessionLineItemRead(id=secret.id, text=secret.text, sort_order=secret.sort_order)
            for secret in session.secrets
        ],
        characters=[
            SessionCharacterRead(
                id=npc.id,
                name=npc.name,
                role_occupation=npc.role_occupation,
                alignment=npc.alignment,
                alignment_display=ALIGNMENT_DISPLAY[npc.alignment],
            )
            for npc in session.characters
        ],
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _serialize_endpoint(kind: str, npc_id: int | None, label: str) -> GraphEndpointRead:
    return GraphEndpointRead(kind=kind, npc_id=npc_id, label=label)


def _endpoint_label(graph: CharacterGraph, kind: str, npc_id: int | None) -> str:
    for node in graph.nodes:
        if node.kind == kind and node.npc_id == npc_id:
            return node_label(node)
    if kind == "party":
        return "Party"
    return "Unknown"


def serialize_graph_node(node: GraphNode) -> GraphNodeRead:
    return GraphNodeRead(
        id=node.id,
        kind=node.kind,
        npc_id=node.npc_id,
        label=node_label(node),
        pos_x=node.pos_x,
        pos_y=node.pos_y,
    )


def serialize_graph_edge(graph: CharacterGraph, edge: GraphEdge) -> GraphEdgeRead:
    return GraphEdgeRead(
        id=edge.id,
        relation_type=RelationTypeRead.model_validate(edge.relation_type),
        from_endpoint=_serialize_endpoint(
            edge.from_kind,
            edge.from_npc_id,
            _endpoint_label(graph, edge.from_kind, edge.from_npc_id),
        ),
        to_endpoint=_serialize_endpoint(
            edge.to_kind,
            edge.to_npc_id,
            _endpoint_label(graph, edge.to_kind, edge.to_npc_id),
        ),
        notes=edge.notes,
    )


def serialize_graph_list(
    graph: CharacterGraph,
    *,
    node_count: int | None = None,
    edge_count: int | None = None,
) -> GraphListRead:
    return GraphListRead(
        id=graph.id,
        campaign=graph.campaign_id,
        name=graph.name,
        notes=graph.notes,
        node_count=node_count if node_count is not None else len(graph.nodes),
        edge_count=edge_count if edge_count is not None else len(graph.edges),
        created_at=graph.created_at,
        updated_at=graph.updated_at,
    )


def serialize_graph_detail(graph: CharacterGraph) -> GraphDetailRead:
    return GraphDetailRead(
        id=graph.id,
        campaign=graph.campaign_id,
        name=graph.name,
        notes=graph.notes,
        nodes=[serialize_graph_node(node) for node in graph.nodes],
        edges=[serialize_graph_edge(graph, edge) for edge in graph.edges],
        created_at=graph.created_at,
        updated_at=graph.updated_at,
    )


def serialize_relation_type(relation_type) -> RelationTypeRead:
    return RelationTypeRead.model_validate(relation_type)
