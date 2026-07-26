from fastapi import Request

from app.constants import ALIGNMENT_DISPLAY
from app.media import build_media_url
from app.models import Campaign, NPC
from app.schemas import (
    AliasRead,
    CampaignListRead,
    CampaignRead,
    NPCDetailRead,
    NPCListRead,
    TagRead,
)


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
