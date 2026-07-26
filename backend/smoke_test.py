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
