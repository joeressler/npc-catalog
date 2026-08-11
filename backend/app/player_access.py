"""Helpers for player-role visibility checks and 404-on-hidden semantics."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.auth import Role, session_role
from app.models import NPC, Campaign, CharacterGraph, Location


def request_role(request: Request) -> Role | None:
    return getattr(request.state, "role", None) or session_role(request)


def is_player(request: Request) -> bool:
    return request_role(request) == "player"


def deny_players(request: Request) -> None:
    """Sessions and encounters are never visible to players."""
    if is_player(request):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found.")


def ensure_campaign_visible(campaign: Campaign, *, for_player: bool) -> Campaign:
    if for_player and not campaign.player_visible:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return campaign


def ensure_npc_visible(npc: NPC, *, for_player: bool) -> NPC:
    if for_player:
        if not npc.player_visible:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NPC not found.")
        campaign = npc.campaign
        if campaign is None or not campaign.player_visible:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NPC not found.")
    return npc


def ensure_location_visible(location: Location, *, for_player: bool) -> Location:
    if for_player:
        if not location.player_visible:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Location not found.")
        campaign = location.campaign
        if campaign is None or not campaign.player_visible:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Location not found.")
    return location


def ensure_graph_visible(graph: CharacterGraph, *, for_player: bool) -> CharacterGraph:
    if for_player:
        if not graph.player_visible:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Graph not found.")
        campaign = graph.campaign
        if campaign is None or not campaign.player_visible:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Graph not found.")
    return graph


def parse_bool_form(value: object | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off", ""}:
        return False
    return default
