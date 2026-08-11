from fastapi import Request

from app.constants import ALIGNMENT_DISPLAY
from app.media import build_media_url
from app.models import (
    NPC,
    Campaign,
    CharacterGraph,
    Encounter,
    GameSession,
    GraphEdge,
    GraphNode,
    Location,
)
from app.schemas import (
    AliasRead,
    CampaignListRead,
    CampaignRead,
    CatalogLocationRead,
    EncounterDetailRead,
    EncounterEnemyRead,
    EncounterListRead,
    EncounterLootRead,
    EncounterNpcRead,
    EncounterObjectRead,
    GraphDetailRead,
    GraphEdgeRead,
    GraphEndpointRead,
    GraphListRead,
    GraphNodeRead,
    LocationDetailRead,
    LocationListRead,
    LocationLootRead,
    LocationNpcRead,
    LocationObjectRead,
    NPCDetailRead,
    NPCListRead,
    RelationTypeRead,
    SessionDetailRead,
    SessionEncounterRead,
    SessionLineItemRead,
    SessionListRead,
    SessionLocationRead,
    SessionNpcRead,
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
        "player_visible": bool(campaign.player_visible),
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
    }
    if npc_count is not None:
        return CampaignListRead(**data, npc_count=npc_count)
    return CampaignRead(**data)


def serialize_npc_list(npc: NPC, request: Request | None = None) -> NPCListRead:
    image = build_media_url(str(request.base_url), npc.image_path) if request else None
    catalog_location = None
    if npc.catalog_location is not None:
        catalog_location = CatalogLocationRead(
            id=npc.catalog_location.id,
            title=npc.catalog_location.title,
        )
    return NPCListRead(
        id=npc.id,
        campaign=npc.campaign_id,
        name=npc.name,
        role_occupation=npc.role_occupation,
        alignment=npc.alignment,
        alignment_display=ALIGNMENT_DISPLAY[npc.alignment],
        location=npc.location,
        catalog_location=catalog_location,
        faction=npc.faction,
        attitude=npc.attitude,
        party_relationship=npc.party_relationship,
        image=image,
        player_visible=bool(npc.player_visible),
        aliases=[AliasRead.model_validate(alias) for alias in npc.aliases],
        tags=[TagRead.model_validate(tag) for tag in npc.tags],
        created_at=npc.created_at,
        updated_at=npc.updated_at,
    )


def serialize_npc_detail(
    npc: NPC,
    request: Request | None = None,
    *,
    for_player: bool = False,
) -> NPCDetailRead:
    base = serialize_npc_list(npc, request)
    if for_player:
        return NPCDetailRead(
            **base.model_dump(),
            appearance=npc.appearance,
            voice_mannerisms=npc.voice_mannerisms,
            personality_traits=npc.personality_traits,
            motivation_goal="",
            secret_hook="",
            knowledge="",
            inventory="",
            dm_notes="",
            session_log="",
        )
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


def serialize_session_list(session: GameSession, *, npc_count: int | None = None) -> SessionListRead:
    count = npc_count if npc_count is not None else len(session.npcs)
    return SessionListRead(
        id=session.id,
        campaign=session.campaign_id,
        number=session.number,
        title=session.title,
        npc_count=count,
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
        npcs=[
            SessionNpcRead(
                id=npc.id,
                name=npc.name,
                role_occupation=npc.role_occupation,
                alignment=npc.alignment,
                alignment_display=ALIGNMENT_DISPLAY[npc.alignment],
            )
            for npc in session.npcs
        ],
        encounters=[
            SessionEncounterRead(
                id=encounter.id,
                title=encounter.title,
                short_description=encounter.short_description,
            )
            for encounter in session.encounters
        ],
        locations=[
            SessionLocationRead(
                id=location.id,
                title=location.title,
                description=location.description,
            )
            for location in session.locations
        ],
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def serialize_encounter_list(
    encounter: Encounter,
    *,
    enemy_count: int | None = None,
    npc_count: int | None = None,
) -> EncounterListRead:
    return EncounterListRead(
        id=encounter.id,
        campaign=encounter.campaign_id,
        title=encounter.title,
        short_description=encounter.short_description,
        enemy_count=enemy_count if enemy_count is not None else len(encounter.enemies),
        npc_count=npc_count if npc_count is not None else len(encounter.npcs),
        created_at=encounter.created_at,
        updated_at=encounter.updated_at,
    )


def serialize_encounter_detail(encounter: Encounter) -> EncounterDetailRead:
    return EncounterDetailRead(
        id=encounter.id,
        campaign=encounter.campaign_id,
        title=encounter.title,
        short_description=encounter.short_description,
        battlefield_description=encounter.battlefield_description,
        further_notes=encounter.further_notes,
        enemies=[
            EncounterEnemyRead(
                id=enemy.id,
                quantity=enemy.quantity,
                name=enemy.name,
                creature_type=enemy.creature_type,
                sort_order=enemy.sort_order,
            )
            for enemy in encounter.enemies
        ],
        loot=[
            EncounterLootRead(
                id=item.id,
                description=item.description,
                sort_order=item.sort_order,
            )
            for item in encounter.loot
        ],
        objects=[
            EncounterObjectRead(
                id=obj.id,
                name=obj.name,
                description=obj.description,
                sort_order=obj.sort_order,
            )
            for obj in encounter.objects
        ],
        npcs=[
            EncounterNpcRead(
                id=npc.id,
                name=npc.name,
                role_occupation=npc.role_occupation,
                alignment=npc.alignment,
                alignment_display=ALIGNMENT_DISPLAY[npc.alignment],
            )
            for npc in encounter.npcs
        ],
        created_at=encounter.created_at,
        updated_at=encounter.updated_at,
    )


def _serialize_location_npc(npc: NPC) -> LocationNpcRead:
    return LocationNpcRead(
        id=npc.id,
        name=npc.name,
        role_occupation=npc.role_occupation,
        alignment=npc.alignment,
        alignment_display=ALIGNMENT_DISPLAY[npc.alignment],
    )


def serialize_location_list(
    location: Location,
    request: Request,
    *,
    npc_count: int | None = None,
    for_player: bool = False,
) -> LocationListRead:
    linked = npc_count
    if linked is None:
        residents = [
            npc for npc in location.residents if (not for_player or npc.player_visible)
        ]
        linked_npcs = [
            npc for npc in location.npcs if (not for_player or npc.player_visible)
        ]
        resident_ids = {npc.id for npc in residents}
        linked_ids = {npc.id for npc in linked_npcs}
        linked = len(resident_ids | linked_ids)
    return LocationListRead(
        id=location.id,
        campaign=location.campaign_id,
        title=location.title,
        description=location.description,
        image=build_media_url(str(request.base_url), location.image_path),
        player_visible=bool(location.player_visible),
        npc_count=linked,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


def serialize_location_detail(
    location: Location,
    request: Request,
    *,
    for_player: bool = False,
) -> LocationDetailRead:
    loot = []
    if not for_player:
        loot = [
            LocationLootRead(
                id=item.id,
                description=item.description,
                sort_order=item.sort_order,
            )
            for item in location.loot
        ]
    npcs = [
        _serialize_location_npc(npc)
        for npc in location.npcs
        if not for_player or npc.player_visible
    ]
    residents = [
        _serialize_location_npc(npc)
        for npc in location.residents
        if not for_player or npc.player_visible
    ]
    return LocationDetailRead(
        id=location.id,
        campaign=location.campaign_id,
        title=location.title,
        description=location.description,
        image=build_media_url(str(request.base_url), location.image_path),
        player_visible=bool(location.player_visible),
        loot=loot,
        objects=[
            LocationObjectRead(
                id=obj.id,
                name=obj.name,
                description=obj.description,
                sort_order=obj.sort_order,
            )
            for obj in location.objects
        ],
        npcs=npcs,
        residents=residents,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


def _serialize_endpoint(node: GraphNode) -> GraphEndpointRead:
    return GraphEndpointRead(
        node_id=node.id,
        kind=node.kind,
        npc_id=node.npc_id,
        label=node_label(node),
    )


def serialize_graph_node(node: GraphNode) -> GraphNodeRead:
    return GraphNodeRead(
        id=node.id,
        kind=node.kind,
        npc_id=node.npc_id,
        label=node_label(node),
        pos_x=node.pos_x,
        pos_y=node.pos_y,
    )


def serialize_graph_edge(edge: GraphEdge, *, for_player: bool = False) -> GraphEdgeRead:
    return GraphEdgeRead(
        id=edge.id,
        relation_type=RelationTypeRead.model_validate(edge.relation_type),
        from_endpoint=_serialize_endpoint(edge.from_node),
        to_endpoint=_serialize_endpoint(edge.to_node),
        notes="" if for_player else edge.notes,
    )


def serialize_graph_list(
    graph: CharacterGraph,
    *,
    node_count: int | None = None,
    edge_count: int | None = None,
    for_player: bool = False,
) -> GraphListRead:
    return GraphListRead(
        id=graph.id,
        campaign=graph.campaign_id,
        name=graph.name,
        notes="" if for_player else graph.notes,
        player_visible=bool(graph.player_visible),
        node_count=node_count if node_count is not None else len(graph.nodes),
        edge_count=edge_count if edge_count is not None else len(graph.edges),
        created_at=graph.created_at,
        updated_at=graph.updated_at,
    )


def serialize_graph_detail(
    graph: CharacterGraph,
    *,
    for_player: bool = False,
) -> GraphDetailRead:
    return GraphDetailRead(
        id=graph.id,
        campaign=graph.campaign_id,
        name=graph.name,
        notes="" if for_player else graph.notes,
        player_visible=bool(graph.player_visible),
        nodes=[serialize_graph_node(node) for node in graph.nodes],
        edges=[serialize_graph_edge(edge, for_player=for_player) for edge in graph.edges],
        created_at=graph.created_at,
        updated_at=graph.updated_at,
    )


def serialize_relation_type(relation_type) -> RelationTypeRead:
    return RelationTypeRead.model_validate(relation_type)
