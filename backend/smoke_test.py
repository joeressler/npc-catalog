"""Smoke test the FastAPI backend API contract."""

import http.cookiejar
import json
import os
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api"
ROOT = BASE[: -len("/api")] if BASE.endswith("/api") else BASE.rsplit("/api", 1)[0]
AUTH_USERNAME = os.environ.get("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "admin")

COOKIE_JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIE_JAR))


def request(
    method: str,
    path: str,
    data: dict | None = None,
    multipart: dict | None = None,
    *,
    authed: bool = True,
    expect_error: int | None = None,
):
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
    opener = OPENER if authed else urllib.request.build_opener()
    try:
        with opener.open(req) as resp:
            payload = resp.read().decode()
            return resp.status, json.loads(payload) if payload else None
    except urllib.error.HTTPError as exc:
        if expect_error is not None and exc.code == expect_error:
            payload = exc.read().decode()
            return exc.code, json.loads(payload) if payload else None
        raise


def login() -> None:
    status, body = request(
        "POST",
        "/auth/login/",
        data={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )
    assert status == 200, body
    assert body["username"] == AUTH_USERNAME
    print("POST /auth/login/ OK")


def main() -> int:
    status, denied = request("GET", "/campaigns/", authed=False, expect_error=401)
    assert status == 401, denied
    print("GET /campaigns/ unauthenticated → 401 OK")

    status, bad = request(
        "POST",
        "/auth/login/",
        data={"username": AUTH_USERNAME, "password": "wrong-password"},
        authed=False,
        expect_error=401,
    )
    assert status == 401, bad
    print("POST /auth/login/ bad password → 401 OK")

    login()

    status, me = request("GET", "/auth/me/")
    assert status == 200 and me["username"] == AUTH_USERNAME
    print("GET /auth/me/ OK")

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
    status, npc = request(
        "POST",
        f"/campaigns/{campaign_id}/npcs/",
        multipart={"payload": json.dumps(npc_payload)},
    )
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

    status, patched = request(
        "PATCH",
        f"/npcs/{npc_id}/",
        multipart={"payload": json.dumps({"attitude": "Gruff"})},
    )
    assert status == 200 and patched["attitude"] == "Gruff"
    print("PATCH /npcs/{id}/ OK")

    encounter_payload = {
        "title": "Ambush at Weathertop",
        "short_description": "Ringwraiths press the party on the hilltop.",
        "battlefield_description": "Rocky outcrop with sparse cover and a ruined watchtower.",
        "further_notes": "Fleeing into the woods breaks line of sight after 2 rounds.",
        "enemies": [
            {"quantity": 5, "name": "Nazgul", "creature_type": "Wraith"},
            {"quantity": 1, "name": "Witch-king", "creature_type": "Wraith Lord"},
        ],
        "loot": ["Morgul blade shard", "Black riding cloak"],
        "objects": [
            {"name": "Broken beacon brazier", "description": "Can be toppled for difficult terrain."},
            {"name": "Watchtower stair", "description": "Half cover; collapses if damaged twice."},
        ],
        "npc_ids": [npc_id],
    }
    status, encounter = request(
        "POST",
        f"/campaigns/{campaign_id}/encounters/",
        data=encounter_payload,
    )
    assert status == 201, encounter
    assert encounter["title"] == "Ambush at Weathertop"
    assert len(encounter["enemies"]) == 2
    assert encounter["enemies"][0]["quantity"] == 5
    assert encounter["enemies"][0]["creature_type"] == "Wraith"
    assert len(encounter["loot"]) == 2
    assert len(encounter["objects"]) == 2
    assert len(encounter["npcs"]) == 1
    encounter_id = encounter["id"]
    print(f"POST /campaigns/{{id}}/encounters/ OK id={encounter_id}")

    status, encounters = request("GET", f"/campaigns/{campaign_id}/encounters/")
    assert status == 200 and encounters["count"] == 1
    assert encounters["results"][0]["enemy_count"] == 2
    assert encounters["results"][0]["npc_count"] == 1
    print("GET /campaigns/{id}/encounters/ OK")

    status, cloned = request("POST", f"/encounters/{encounter_id}/clone/")
    assert status == 201, cloned
    assert cloned["title"] == "Ambush at Weathertop (copy)"
    assert len(cloned["enemies"]) == 2
    assert cloned["id"] != encounter_id
    cloned_id = cloned["id"]
    print("POST /encounters/{id}/clone/ OK")

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
        "npc_ids": [npc_id],
        "encounter_ids": [encounter_id],
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
    assert len(session["npcs"]) == 1
    assert session["npcs"][0]["id"] == npc_id
    assert len(session["encounters"]) == 1
    assert session["encounters"][0]["id"] == encounter_id
    session_id = session["id"]
    print(f"POST /campaigns/{{id}}/sessions/ OK id={session_id}")

    status, sessions = request("GET", f"/campaigns/{campaign_id}/sessions/")
    assert status == 200 and sessions["count"] == 1
    assert sessions["results"][0]["npc_count"] == 1
    print("GET /campaigns/{id}/sessions/ OK")

    status, session2 = request("POST", f"/campaigns/{campaign_id}/sessions/", data={"title": "Session Two"})
    assert status == 201 and session2["number"] == 2
    assert session2["encounters"] == []
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
        data={"story_paths": reordered_paths, "encounter_ids": [encounter_id, cloned_id]},
    )
    assert status == 200, updated
    assert [beat["text"] for beat in updated["story_paths"][0]["beats"]] == reordered_paths[0]["beats"]
    assert [beat["text"] for beat in updated["story_paths"][1]["beats"]] == reordered_paths[1]["beats"]
    assert len(updated["encounters"]) == 2
    print("PATCH /sessions/{id}/ reorder story paths OK")

    status, detail = request("GET", f"/sessions/{session_id}/")
    assert status == 200 and detail["overall_notes"] == "Party met Gandalf at the crossroads."
    print("GET /sessions/{id}/ OK")

    status, _ = request("DELETE", f"/sessions/{session_id}/")
    assert status == 204
    print("DELETE /sessions/{id}/ OK")

    status, encounter_detail = request("GET", f"/encounters/{encounter_id}/")
    assert status == 200 and encounter_detail["title"] == "Ambush at Weathertop"
    print("GET /encounters/{id}/ OK after session delete")

    status, _ = request("DELETE", f"/encounters/{encounter_id}/")
    assert status == 204
    status, _ = request("DELETE", f"/encounters/{cloned_id}/")
    assert status == 204
    print("DELETE /encounters/{id}/ OK")

    status, global_list = request("GET", "/npcs/?alignment=NG")
    assert status == 200 and global_list["count"] >= 1
    print("GET /npcs/ OK")

    # Media path is gated the same way as /api.
    media_req = urllib.request.Request(f"{ROOT}/media/")
    try:
        urllib.request.urlopen(media_req)
        raise AssertionError("unauthenticated /media/ should 401")
    except urllib.error.HTTPError as exc:
        assert exc.code == 401
    print("GET /media/ unauthenticated → 401 OK")

    status, _ = request("POST", "/auth/logout/")
    assert status == 200
    status, denied_again = request("GET", "/campaigns/", expect_error=401)
    assert status == 401, denied_again
    print("POST /auth/logout/ OK")

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
