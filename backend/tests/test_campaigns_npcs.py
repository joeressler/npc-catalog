"""Tests for campaigns and NPC CRUD + filtering."""
import json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_campaign(client, name="Test Campaign"):
    r = client.post("/api/campaigns/", data={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


def _create_npc(client, campaign_id, *, name="Gandalf", role_occupation="Wizard",
                alignment="NG", location="Middle-earth", faction="",
                attitude="Friendly", party_relationship="Ally",
                aliases=None, tags=None):
    payload = {
        "name": name,
        "role_occupation": role_occupation,
        "alignment": alignment,
        "location": location,
        "faction": faction,
        "attitude": attitude,
        "party_relationship": party_relationship,
        "aliases": aliases or [],
        "tags": tags or [],
    }
    r = client.post(
        f"/api/campaigns/{campaign_id}/npcs/",
        data={"payload": json.dumps(payload)},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Campaign tests
# ---------------------------------------------------------------------------

def test_create_campaign(client):
    data = _create_campaign(client, "Dragon Hunters")
    assert data["name"] == "Dragon Hunters"
    assert isinstance(data["id"], int)
    assert "created_at" in data
    assert "updated_at" in data


def test_list_campaigns(client):
    _create_campaign(client, "Campaign Alpha")
    _create_campaign(client, "Campaign Beta")
    r = client.get("/api/campaigns/")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2
    names = [c["name"] for c in data["results"]]
    assert "Campaign Alpha" in names
    assert "Campaign Beta" in names


def test_get_campaign(client):
    created = _create_campaign(client, "Get Me")
    r = client.get(f"/api/campaigns/{created['id']}/")
    assert r.status_code == 200
    assert r.json()["name"] == "Get Me"


# ---------------------------------------------------------------------------
# NPC tests
# ---------------------------------------------------------------------------

def test_create_npc_basic(client):
    campaign = _create_campaign(client)
    npc = _create_npc(client, campaign["id"])
    assert npc["name"] == "Gandalf"
    assert npc["alignment"] == "NG"
    assert npc["alignment_display"] == "Neutral Good"
    assert npc["campaign"] == campaign["id"]
    # detail fields present
    assert "appearance" in npc
    assert "voice_mannerisms" in npc
    assert "dm_notes" in npc


def test_create_npc_with_aliases_and_tags(client):
    campaign = _create_campaign(client)
    npc = _create_npc(
        client,
        campaign["id"],
        aliases=["Mithrandir", "Grey Pilgrim"],
        tags=["ally", "wizard"],
    )
    alias_names = [a["name"] for a in npc["aliases"]]
    tag_names = [t["name"] for t in npc["tags"]]
    assert "Mithrandir" in alias_names
    assert "Grey Pilgrim" in alias_names
    assert "ally" in tag_names
    assert "wizard" in tag_names


# ---------------------------------------------------------------------------
# Filter tests
# ---------------------------------------------------------------------------

def test_filter_npcs_by_q_role_occupation(client):
    campaign = _create_campaign(client)
    _create_npc(client, campaign["id"], name="Gandalf", role_occupation="Wizard")
    _create_npc(client, campaign["id"], name="Saruman", role_occupation="Wizard")
    _create_npc(client, campaign["id"], name="Frodo", role_occupation="Ring-bearer")

    r = client.get(f"/api/campaigns/{campaign['id']}/npcs/?q=wizard")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2
    names = {n["name"] for n in data["results"]}
    assert names == {"Gandalf", "Saruman"}


def test_filter_npcs_by_q_name_partial(client):
    campaign = _create_campaign(client)
    _create_npc(client, campaign["id"], name="Gandalf the Grey", role_occupation="Wizard")
    _create_npc(client, campaign["id"], name="Frodo", role_occupation="Hobbit")

    r = client.get(f"/api/campaigns/{campaign['id']}/npcs/?q=gandalf")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Gandalf the Grey"


def test_filter_npcs_by_q_alias(client):
    campaign = _create_campaign(client)
    _create_npc(client, campaign["id"], name="Gandalf", aliases=["Mithrandir"])
    _create_npc(client, campaign["id"], name="Frodo")

    r = client.get(f"/api/campaigns/{campaign['id']}/npcs/?q=mithrandir")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Gandalf"


def test_filter_npcs_by_tag(client):
    campaign = _create_campaign(client)
    _create_npc(client, campaign["id"], name="Gandalf", tags=["wizard", "ally"])
    _create_npc(client, campaign["id"], name="Saruman", tags=["wizard", "villain"])
    _create_npc(client, campaign["id"], name="Frodo", tags=["hobbit"])

    r = client.get(f"/api/campaigns/{campaign['id']}/npcs/?tag=wizard")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2
    names = {n["name"] for n in data["results"]}
    assert names == {"Gandalf", "Saruman"}


def test_filter_npcs_by_tag_single(client):
    campaign = _create_campaign(client)
    _create_npc(client, campaign["id"], name="Gandalf", tags=["wizard", "ally"])
    _create_npc(client, campaign["id"], name="Saruman", tags=["wizard", "villain"])

    r = client.get(f"/api/campaigns/{campaign['id']}/npcs/?tag=ally")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Gandalf"


def test_filter_npcs_no_results(client):
    campaign = _create_campaign(client)
    _create_npc(client, campaign["id"], name="Gandalf")

    r = client.get(f"/api/campaigns/{campaign['id']}/npcs/?q=nonexistent_xyz")
    assert r.status_code == 200
    assert r.json()["count"] == 0
