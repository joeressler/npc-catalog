"""Smoke test the FastAPI backend API contract."""

import json
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api"


def request(method: str, path: str, data: dict | None = None, multipart: dict | None = None):
    url = f"{BASE}{path}"
    headers = {}
    body = None

    if multipart is not None:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        parts = []
        for key, value in multipart.items():
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n")
        parts.append(f"--{boundary}--\r\n")
        body = "".join(parts).encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        payload = resp.read().decode()
        return resp.status, json.loads(payload) if payload else None


def main() -> int:
    status, campaigns = request("GET", "/campaigns/")
    assert status == 200, campaigns
    assert "count" in campaigns and "results" in campaigns
    print("GET /campaigns/ OK")

    unique_name = f"Smoke Test Campaign {uuid.uuid4().hex[:8]}"
    status, campaign = request("POST", "/campaigns/", multipart={"name": unique_name})
    assert status == 201, campaign
    assert campaign["id"] and campaign["name"] == unique_name
    campaign_id = campaign["id"]
    print(f"POST /campaigns/ OK id={campaign_id}")

    npc_payload = {
        "name": "Gandalf",
        "role_occupation": "Wizard",
        "alignment": "NG",
        "location": "Middle-earth",
        "faction": "",
        "attitude": "Friendly",
        "party_relationship": "Ally",
        "aliases": ["Mithrandir", "Grey Pilgrim"],
        "tags": ["ally", "wizard"],
    }
    status, npc = request("POST", f"/campaigns/{campaign_id}/npcs/", data=npc_payload)
    assert status == 201, npc
    assert npc["alignment_display"] == "Neutral Good"
    assert len(npc["aliases"]) == 2
    assert len(npc["tags"]) == 2
    assert "appearance" in npc
    npc_id = npc["id"]
    print(f"POST /campaigns/{{id}}/npcs/ OK id={npc_id}")

    status, filtered = request("GET", f"/campaigns/{campaign_id}/npcs/?q=wizard")
    assert status == 200 and filtered["count"] == 1
    print("GET /campaigns/{id}/npcs/?q= OK")

    status, tags = request("GET", "/tags/")
    assert status == 200 and tags["count"] >= 2
    print("GET /tags/ OK")

    status, detail = request("GET", f"/npcs/{npc_id}/")
    assert status == 200 and detail["session_log"] == ""
    print("GET /npcs/{id}/ OK")

    status, patched = request("PATCH", f"/npcs/{npc_id}/", data={"attitude": "Gruff"})
    assert status == 200 and patched["attitude"] == "Gruff"
    print("PATCH /npcs/{id}/ OK")

    session_payload = {
        "title": "The Grey Council",
        "overall_notes": "Party met Gandalf at the crossroads.",
        "story_paths": [
            {
                "name": "Main timeline",
                "beats": ["Arrival at camp", "Gandalf reveals the quest", "Departure at dawn"],
            },
            {
                "name": "If the party refuses the quest",
                "beats": ["They linger in Bree", "A rival wizard intervenes"],
            },
        ],
        "clues": ["Strange tracks near the river"],
        "secrets": ["Gandalf knows more than he admits"],
        "character_ids": [npc_id],
    }
    status, session = request("POST", f"/campaigns/{campaign_id}/sessions/", data=session_payload)
    assert status == 201, session
    assert session["number"] == 1
    assert session["title"] == "The Grey Council"
    assert len(session["story_paths"]) == 2
    assert session["story_paths"][0]["name"] == "Main timeline"
    assert len(session["story_paths"][0]["beats"]) == 3
    assert session["story_paths"][0]["beats"][0]["text"] == "Arrival at camp"
    assert session["story_paths"][0]["beats"][0]["sort_order"] == 0
    assert session["story_paths"][1]["beats"][0]["text"] == "They linger in Bree"
    assert len(session["characters"]) == 1
    assert session["characters"][0]["id"] == npc_id
    session_id = session["id"]
    print(f"POST /campaigns/{{id}}/sessions/ OK id={session_id}")

    status, sessions = request("GET", f"/campaigns/{campaign_id}/sessions/")
    assert status == 200 and sessions["count"] == 1
    assert sessions["results"][0]["character_count"] == 1
    print("GET /campaigns/{id}/sessions/ OK")

    status, session2 = request("POST", f"/campaigns/{campaign_id}/sessions/", data={"title": "Session Two"})
    assert status == 201 and session2["number"] == 2
    print("POST auto-number session 2 OK")

    reordered_paths = [
        {
            "name": "Main timeline",
            "beats": ["Departure at dawn", "Arrival at camp", "Gandalf reveals the quest"],
        },
        {
            "name": "If the party refuses the quest",
            "beats": ["A rival wizard intervenes", "They linger in Bree"],
        },
    ]
    status, updated = request(
        "PATCH",
        f"/sessions/{session_id}/",
        data={"story_paths": reordered_paths},
    )
    assert status == 200, updated
    assert [beat["text"] for beat in updated["story_paths"][0]["beats"]] == reordered_paths[0]["beats"]
    assert [beat["text"] for beat in updated["story_paths"][1]["beats"]] == reordered_paths[1]["beats"]
    print("PATCH /sessions/{id}/ reorder story paths OK")

    status, detail = request("GET", f"/sessions/{session_id}/")
    assert status == 200 and detail["overall_notes"] == "Party met Gandalf at the crossroads."
    print("GET /sessions/{id}/ OK")

    status, _ = request("DELETE", f"/sessions/{session_id}/")
    assert status == 204
    print("DELETE /sessions/{id}/ OK")

    status, global_list = request("GET", "/npcs/?alignment=NG")
    assert status == 200 and global_list["count"] >= 1
    print("GET /npcs/ OK")

    print("ALL SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}: {exc.read().decode()}", file=sys.stderr)
        raise SystemExit(1) from exc
    except AssertionError as exc:
        print(f"ASSERT FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
