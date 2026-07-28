"""Tests for character relationship graphs, nodes, edges, and relation types."""
import json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_campaign(client, name="Graph Campaign"):
    r = client.post("/api/campaigns/", data={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


def _create_npc(client, campaign_id, name="Gandalf"):
    payload = {
        "name": name,
        "role_occupation": "Wizard",
        "alignment": "NG",
        "location": "",
        "faction": "",
        "attitude": "Friendly",
        "party_relationship": "Ally",
        "aliases": [],
        "tags": [],
    }
    r = client.post(
        f"/api/campaigns/{campaign_id}/npcs/",
        data={"payload": json.dumps(payload)},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _create_graph(client, campaign_id, name="Test Graph", notes=""):
    r = client.post(
        f"/api/campaigns/{campaign_id}/graphs/",
        json={"name": name, "notes": notes},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _get_relation_type_id(client, campaign_id, name="Ally"):
    """Return the id of the named relation type in the campaign (must exist)."""
    r = client.get(f"/api/campaigns/{campaign_id}/relation-types/")
    assert r.status_code == 200
    for rt in r.json()["results"]:
        if rt["name"] == name:
            return rt["id"]
    raise AssertionError(f"Relation type '{name}' not found in campaign {campaign_id}")


def _add_node(client, graph_id, kind, npc_id=None, label=None):
    payload = {"kind": kind}
    if npc_id is not None:
        payload["npc_id"] = npc_id
    if label is not None:
        payload["label"] = label
    r = client.post(f"/api/graphs/{graph_id}/nodes/", json=payload)
    return r


# ---------------------------------------------------------------------------
# Relation type / defaults tests
# ---------------------------------------------------------------------------

def test_campaign_create_seeds_relation_types(client):
    """Creating a campaign seeds all default relation types."""
    from app.constants import DEFAULT_RELATION_TYPES

    campaign = _create_campaign(client)
    r = client.get(f"/api/campaigns/{campaign['id']}/relation-types/")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == len(DEFAULT_RELATION_TYPES)
    names = {rt["name"] for rt in data["results"]}
    # Spot-check a few expected defaults
    assert "Ally" in names
    assert "Enemy" in names
    assert "Trusts" in names
    assert "Frenemies" in names


def test_add_relation_type(client):
    campaign = _create_campaign(client)
    r = client.post(
        f"/api/campaigns/{campaign['id']}/relation-types/",
        json={"name": "Soul Bond", "polarity": "positive"},
    )
    assert r.status_code == 201
    rt = r.json()
    assert rt["name"] == "Soul Bond"
    assert rt["polarity"] == "positive"
    assert isinstance(rt["id"], int)


def test_add_duplicate_relation_type_rejected(client):
    campaign = _create_campaign(client)
    # "Ally" is already seeded
    r = client.post(
        f"/api/campaigns/{campaign['id']}/relation-types/",
        json={"name": "Ally", "polarity": "positive"},
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Graph CRUD tests
# ---------------------------------------------------------------------------

def test_create_graph(client):
    campaign = _create_campaign(client)
    graph = _create_graph(client, campaign["id"], name="Web of Fate")
    assert graph["name"] == "Web of Fate"
    assert graph["campaign"] == campaign["id"]
    assert graph["nodes"] == []
    assert graph["edges"] == []
    assert isinstance(graph["id"], int)


def test_list_campaign_graphs(client):
    campaign = _create_campaign(client)
    _create_graph(client, campaign["id"], name="Graph A")
    _create_graph(client, campaign["id"], name="Graph B")
    r = client.get(f"/api/campaigns/{campaign['id']}/graphs/")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2


def test_delete_graph(client):
    campaign = _create_campaign(client)
    graph = _create_graph(client, campaign["id"])
    r = client.delete(f"/api/graphs/{graph['id']}/")
    assert r.status_code == 204
    r = client.get(f"/api/graphs/{graph['id']}/")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Node tests
# ---------------------------------------------------------------------------

def test_add_npc_node(client):
    campaign = _create_campaign(client)
    npc = _create_npc(client, campaign["id"])
    graph = _create_graph(client, campaign["id"])

    r = _add_node(client, graph["id"], kind="npc", npc_id=npc["id"])
    assert r.status_code == 201
    node = r.json()
    assert node["kind"] == "npc"
    assert node["npc_id"] == npc["id"]
    assert node["label"] == npc["name"]


def test_add_party_node(client):
    campaign = _create_campaign(client)
    graph = _create_graph(client, campaign["id"])

    r = _add_node(client, graph["id"], kind="party")
    assert r.status_code == 201
    node = r.json()
    assert node["kind"] == "party"
    assert node["npc_id"] is None


def test_add_duplicate_party_node_rejected(client):
    campaign = _create_campaign(client)
    graph = _create_graph(client, campaign["id"])

    _add_node(client, graph["id"], kind="party")
    r = _add_node(client, graph["id"], kind="party")
    assert r.status_code == 400


def test_add_pc_node_requires_party_first(client):
    """Adding a PC node before a Party node must return 400."""
    campaign = _create_campaign(client)
    graph = _create_graph(client, campaign["id"])

    r = _add_node(client, graph["id"], kind="pc", label="Frodo")
    assert r.status_code == 400
    detail = r.json().get("detail", "")
    assert "Party" in detail or "party" in detail


def test_add_pc_node_after_party(client):
    campaign = _create_campaign(client)
    graph = _create_graph(client, campaign["id"])

    _add_node(client, graph["id"], kind="party")
    r = _add_node(client, graph["id"], kind="pc", label="Frodo")
    assert r.status_code == 201
    node = r.json()
    assert node["kind"] == "pc"
    assert node["label"] == "Frodo"


def test_add_multiple_pc_nodes(client):
    campaign = _create_campaign(client)
    graph = _create_graph(client, campaign["id"])

    _add_node(client, graph["id"], kind="party")
    r1 = _add_node(client, graph["id"], kind="pc", label="Frodo")
    r2 = _add_node(client, graph["id"], kind="pc", label="Sam")
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["label"] == "Frodo"
    assert r2.json()["label"] == "Sam"


def test_update_node_position(client):
    campaign = _create_campaign(client)
    npc = _create_npc(client, campaign["id"])
    graph = _create_graph(client, campaign["id"])
    node = _add_node(client, graph["id"], kind="npc", npc_id=npc["id"]).json()

    r = client.patch(f"/api/graph-nodes/{node['id']}/", json={"pos_x": 42.5, "pos_y": 77.0})
    assert r.status_code == 200
    updated = r.json()
    assert updated["pos_x"] == 42.5
    assert updated["pos_y"] == 77.0


def test_delete_pc_node(client):
    campaign = _create_campaign(client)
    graph = _create_graph(client, campaign["id"])
    _add_node(client, graph["id"], kind="party")
    pc_node = _add_node(client, graph["id"], kind="pc", label="Sam").json()

    r = client.delete(f"/api/graph-nodes/{pc_node['id']}/")
    assert r.status_code == 204

    graph_detail = client.get(f"/api/graphs/{graph['id']}/").json()
    node_ids = {n["id"] for n in graph_detail["nodes"]}
    assert pc_node["id"] not in node_ids


def test_delete_party_node_cascades_pc_nodes(client):
    """Deleting the Party node must also remove all PC child nodes."""
    campaign = _create_campaign(client)
    graph = _create_graph(client, campaign["id"])
    party = _add_node(client, graph["id"], kind="party").json()
    _add_node(client, graph["id"], kind="pc", label="Frodo")
    _add_node(client, graph["id"], kind="pc", label="Sam")

    r = client.delete(f"/api/graph-nodes/{party['id']}/")
    assert r.status_code == 204

    graph_detail = client.get(f"/api/graphs/{graph['id']}/").json()
    assert graph_detail["nodes"] == []


# ---------------------------------------------------------------------------
# Edge tests
# ---------------------------------------------------------------------------

def test_add_directed_edge(client):
    campaign = _create_campaign(client)
    npc_a = _create_npc(client, campaign["id"], name="Frodo")
    npc_b = _create_npc(client, campaign["id"], name="Sam")
    graph = _create_graph(client, campaign["id"])
    node_a = _add_node(client, graph["id"], kind="npc", npc_id=npc_a["id"]).json()
    node_b = _add_node(client, graph["id"], kind="npc", npc_id=npc_b["id"]).json()
    rt_id = _get_relation_type_id(client, campaign["id"], "Ally")

    r = client.post(f"/api/graphs/{graph['id']}/edges/", json={
        "relation_type_id": rt_id,
        "from_node_id": node_a["id"],
        "to_node_id": node_b["id"],
        "notes": "Best friends",
        "bidirectional": False,
    })
    assert r.status_code == 201
    edge = r.json()
    assert edge["from_endpoint"]["node_id"] == node_a["id"]
    assert edge["to_endpoint"]["node_id"] == node_b["id"]
    assert edge["relation_type"]["name"] == "Ally"
    assert edge["notes"] == "Best friends"

    # Only one edge was created
    graph_detail = client.get(f"/api/graphs/{graph['id']}/").json()
    assert len(graph_detail["edges"]) == 1


def test_add_bidirectional_edge_creates_reverse(client):
    campaign = _create_campaign(client)
    npc_a = _create_npc(client, campaign["id"], name="Frodo")
    npc_b = _create_npc(client, campaign["id"], name="Sam")
    graph = _create_graph(client, campaign["id"])
    node_a = _add_node(client, graph["id"], kind="npc", npc_id=npc_a["id"]).json()
    node_b = _add_node(client, graph["id"], kind="npc", npc_id=npc_b["id"]).json()
    rt_id = _get_relation_type_id(client, campaign["id"], "Ally")

    r = client.post(f"/api/graphs/{graph['id']}/edges/", json={
        "relation_type_id": rt_id,
        "from_node_id": node_a["id"],
        "to_node_id": node_b["id"],
        "bidirectional": True,
    })
    assert r.status_code == 201

    # Both A→B and B→A edges should exist
    graph_detail = client.get(f"/api/graphs/{graph['id']}/").json()
    assert len(graph_detail["edges"]) == 2
    froms = {e["from_endpoint"]["node_id"] for e in graph_detail["edges"]}
    tos = {e["to_endpoint"]["node_id"] for e in graph_detail["edges"]}
    assert node_a["id"] in froms
    assert node_b["id"] in froms
    assert node_a["id"] in tos
    assert node_b["id"] in tos


def test_delete_edge(client):
    campaign = _create_campaign(client)
    npc_a = _create_npc(client, campaign["id"], name="Frodo")
    npc_b = _create_npc(client, campaign["id"], name="Sam")
    graph = _create_graph(client, campaign["id"])
    node_a = _add_node(client, graph["id"], kind="npc", npc_id=npc_a["id"]).json()
    node_b = _add_node(client, graph["id"], kind="npc", npc_id=npc_b["id"]).json()
    rt_id = _get_relation_type_id(client, campaign["id"], "Ally")

    edge = client.post(f"/api/graphs/{graph['id']}/edges/", json={
        "relation_type_id": rt_id,
        "from_node_id": node_a["id"],
        "to_node_id": node_b["id"],
    }).json()

    r = client.delete(f"/api/graph-edges/{edge['id']}/")
    assert r.status_code == 204

    graph_detail = client.get(f"/api/graphs/{graph['id']}/").json()
    assert graph_detail["edges"] == []


def test_delete_node_removes_incident_edges(client):
    """Deleting a node should cascade-remove its incident edges."""
    campaign = _create_campaign(client)
    npc_a = _create_npc(client, campaign["id"], name="Frodo")
    npc_b = _create_npc(client, campaign["id"], name="Sam")
    graph = _create_graph(client, campaign["id"])
    node_a = _add_node(client, graph["id"], kind="npc", npc_id=npc_a["id"]).json()
    node_b = _add_node(client, graph["id"], kind="npc", npc_id=npc_b["id"]).json()
    rt_id = _get_relation_type_id(client, campaign["id"], "Ally")

    client.post(f"/api/graphs/{graph['id']}/edges/", json={
        "relation_type_id": rt_id,
        "from_node_id": node_a["id"],
        "to_node_id": node_b["id"],
    })

    r = client.delete(f"/api/graph-nodes/{node_a['id']}/")
    assert r.status_code == 204

    graph_detail = client.get(f"/api/graphs/{graph['id']}/").json()
    assert graph_detail["edges"] == []
    remaining_node_ids = {n["id"] for n in graph_detail["nodes"]}
    assert node_a["id"] not in remaining_node_ids
    assert node_b["id"] in remaining_node_ids
