"""Tests for sessions and encounters, including npc_ids linkage."""
import json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_campaign(client, name="Test Campaign"):
    r = client.post("/api/campaigns/", data={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


def _create_npc(client, campaign_id, name="NPC Hero"):
    payload = {
        "name": name,
        "role_occupation": "Fighter",
        "alignment": "N",
        "location": "",
        "faction": "",
        "attitude": "Neutral",
        "party_relationship": "",
        "aliases": [],
        "tags": [],
    }
    r = client.post(
        f"/api/campaigns/{campaign_id}/npcs/",
        data={"payload": json.dumps(payload)},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _create_encounter(client, campaign_id, title="Test Encounter", npc_ids=None,
                      enemies=None, loot=None, objects=None):
    payload = {
        "title": title,
        "short_description": "A dangerous encounter.",
        "battlefield_description": "",
        "further_notes": "",
        "enemies": enemies or [],
        "loot": loot or [],
        "objects": objects or [],
        "npc_ids": npc_ids or [],
    }
    r = client.post(f"/api/campaigns/{campaign_id}/encounters/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _create_session(client, campaign_id, title="Session One", npc_ids=None,
                    encounter_ids=None, story_paths=None, clues=None, secrets=None):
    payload = {
        "title": title,
        "overall_notes": "",
        "npc_ids": npc_ids or [],
        "encounter_ids": encounter_ids or [],
        "story_paths": story_paths or [],
        "clues": clues or [],
        "secrets": secrets or [],
    }
    r = client.post(f"/api/campaigns/{campaign_id}/sessions/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Encounter tests
# ---------------------------------------------------------------------------

def test_create_encounter_basic(client):
    campaign = _create_campaign(client)
    enc = _create_encounter(client, campaign["id"], title="Ambush")
    assert enc["title"] == "Ambush"
    assert enc["campaign"] == campaign["id"]
    assert enc["npcs"] == []
    assert enc["enemies"] == []


def test_create_encounter_with_npc_ids(client):
    campaign = _create_campaign(client)
    npc = _create_npc(client, campaign["id"])
    enc = _create_encounter(client, campaign["id"], npc_ids=[npc["id"]])

    assert len(enc["npcs"]) == 1
    assert enc["npcs"][0]["id"] == npc["id"]
    assert enc["npcs"][0]["name"] == npc["name"]
    # Detail schema has `npcs` list, not character_* fields
    assert "character_ids" not in enc
    assert "character_count" not in enc


def test_create_encounter_with_enemies_and_loot(client):
    campaign = _create_campaign(client)
    enemies = [
        {"quantity": 5, "name": "Orc", "creature_type": "Humanoid"},
        {"quantity": 1, "name": "Troll", "creature_type": "Giant"},
    ]
    loot = ["Gold coin purse", "Magic ring"]
    enc = _create_encounter(client, campaign["id"], enemies=enemies, loot=loot)

    assert len(enc["enemies"]) == 2
    assert enc["enemies"][0]["quantity"] == 5
    assert enc["enemies"][0]["creature_type"] == "Humanoid"
    assert len(enc["loot"]) == 2


def test_clone_encounter(client):
    campaign = _create_campaign(client)
    npc = _create_npc(client, campaign["id"])
    original = _create_encounter(
        client, campaign["id"],
        title="Battle of Helm's Deep",
        npc_ids=[npc["id"]],
        enemies=[{"quantity": 10, "name": "Uruk-hai", "creature_type": "Orc"}],
    )
    r = client.post(f"/api/encounters/{original['id']}/clone/")
    assert r.status_code == 201
    cloned = r.json()
    assert cloned["title"] == "Battle of Helm's Deep (copy)"
    assert cloned["id"] != original["id"]
    assert cloned["campaign"] == campaign["id"]
    assert len(cloned["npcs"]) == 1
    assert len(cloned["enemies"]) == 1


def test_list_encounters_npc_count(client):
    campaign = _create_campaign(client)
    npc1 = _create_npc(client, campaign["id"], name="NPC 1")
    npc2 = _create_npc(client, campaign["id"], name="NPC 2")
    _create_encounter(client, campaign["id"], npc_ids=[npc1["id"], npc2["id"]])

    r = client.get(f"/api/campaigns/{campaign['id']}/encounters/")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    summary = data["results"][0]
    assert summary["npc_count"] == 2
    # List schema uses npc_count, not character_count
    assert "character_count" not in summary


# ---------------------------------------------------------------------------
# Session tests
# ---------------------------------------------------------------------------

def test_create_session_basic(client):
    campaign = _create_campaign(client)
    s = _create_session(client, campaign["id"], title="The Beginning")
    assert s["title"] == "The Beginning"
    assert s["campaign"] == campaign["id"]
    assert s["number"] == 1
    assert s["npcs"] == []
    assert s["encounters"] == []
    assert s["story_paths"] == []


def test_create_session_with_npc_ids(client):
    campaign = _create_campaign(client)
    npc = _create_npc(client, campaign["id"])
    s = _create_session(client, campaign["id"], npc_ids=[npc["id"]])

    assert len(s["npcs"]) == 1
    assert s["npcs"][0]["id"] == npc["id"]
    assert s["npcs"][0]["name"] == npc["name"]
    # Verify correct field names — no character_* fields
    assert "character_ids" not in s
    assert "character_count" not in s


def test_session_auto_number(client):
    campaign = _create_campaign(client)
    s1 = _create_session(client, campaign["id"], title="First")
    s2 = _create_session(client, campaign["id"], title="Second")
    s3 = _create_session(client, campaign["id"], title="Third")
    assert s1["number"] == 1
    assert s2["number"] == 2
    assert s3["number"] == 3


def test_session_list_npc_count(client):
    campaign = _create_campaign(client)
    npc = _create_npc(client, campaign["id"])
    _create_session(client, campaign["id"], title="Counted", npc_ids=[npc["id"]])

    r = client.get(f"/api/campaigns/{campaign['id']}/sessions/")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    summary = data["results"][0]
    assert summary["npc_count"] == 1
    # List summary must not use character_* naming
    assert "character_count" not in summary
    assert "character_ids" not in summary


def test_session_with_encounter_ids(client):
    campaign = _create_campaign(client)
    enc = _create_encounter(client, campaign["id"], title="Trap Room")
    s = _create_session(client, campaign["id"], encounter_ids=[enc["id"]])

    assert len(s["encounters"]) == 1
    assert s["encounters"][0]["id"] == enc["id"]
    assert s["encounters"][0]["title"] == "Trap Room"


def test_reorder_story_paths(client):
    campaign = _create_campaign(client)
    paths = [
        {"name": "Main", "beats": ["Beat A", "Beat B", "Beat C"]},
        {"name": "Alt", "beats": ["Beat X"]},
    ]
    s = _create_session(client, campaign["id"], title="Path Test", story_paths=paths)
    session_id = s["id"]
    assert len(s["story_paths"]) == 2
    assert s["story_paths"][0]["name"] == "Main"

    reordered = [
        {"name": "Alt", "beats": ["Beat X Reordered"]},
        {"name": "Main", "beats": ["Beat C", "Beat A"]},
    ]
    r = client.patch(f"/api/sessions/{session_id}/", json={"story_paths": reordered})
    assert r.status_code == 200
    updated = r.json()
    assert updated["story_paths"][0]["name"] == "Alt"
    assert updated["story_paths"][0]["beats"][0]["text"] == "Beat X Reordered"
    assert updated["story_paths"][1]["name"] == "Main"
    beats = [b["text"] for b in updated["story_paths"][1]["beats"]]
    assert beats == ["Beat C", "Beat A"]


def test_session_clues_and_secrets(client):
    campaign = _create_campaign(client)
    s = _create_session(
        client, campaign["id"],
        clues=["Strange footprints near the river"],
        secrets=["The innkeeper is a spy"],
    )
    assert len(s["clues"]) == 1
    assert s["clues"][0]["text"] == "Strange footprints near the river"
    assert len(s["secrets"]) == 1
    assert s["secrets"][0]["text"] == "The innkeeper is a spy"
