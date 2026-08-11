"""Unit checks for production hardening helpers (no server required)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.config import (
    INSECURE_AUTH_PASSWORD,
    INSECURE_AUTH_PLAYER_PASSWORD,
    INSECURE_AUTH_PLAYER_USERNAME,
    INSECURE_AUTH_SECRET,
    INSECURE_AUTH_USERNAME,
    Settings,
    validate_production_secrets,
)
from app.media import resolve_media_path
from app.services.ai_prompts import build_prompts
from app.services.comfyui import SIZE_BY_KIND, build_workflow


def test_validate_allows_debug_with_insecure_defaults() -> None:
    cfg = Settings(
        debug=True,
        auth_username=INSECURE_AUTH_USERNAME,
        auth_password=INSECURE_AUTH_PASSWORD,
        auth_secret=INSECURE_AUTH_SECRET,
    )
    validate_production_secrets(cfg)


def test_validate_rejects_insecure_when_not_debug() -> None:
    cfg = Settings(
        debug=False,
        auth_username=INSECURE_AUTH_USERNAME,
        auth_password="strong-password-here",
        auth_secret="strong-secret-here",
    )
    try:
        validate_production_secrets(cfg)
    except RuntimeError as exc:
        assert "AUTH_USERNAME" in str(exc)
    else:
        raise AssertionError("expected RuntimeError for insecure username")


def test_validate_rejects_empty_secret_when_not_debug() -> None:
    cfg = Settings(
        debug=False,
        auth_username="dm",
        auth_password="strong-password-here",
        auth_secret="   ",
    )
    try:
        validate_production_secrets(cfg)
    except RuntimeError as exc:
        assert "AUTH_SECRET" in str(exc)
    else:
        raise AssertionError("expected RuntimeError for empty secret")


def test_validate_accepts_strong_secrets_when_not_debug() -> None:
    cfg = Settings(
        debug=False,
        auth_username="dungeon-master",
        auth_password="correct-horse-battery-staple",
        auth_player_username="table-player",
        auth_player_password="player-horse-battery-staple",
        auth_secret="a-long-random-signing-secret",
    )
    validate_production_secrets(cfg)


def test_validate_rejects_insecure_player_password_when_not_debug() -> None:
    cfg = Settings(
        debug=False,
        auth_username="dungeon-master",
        auth_password="correct-horse-battery-staple",
        auth_player_username=INSECURE_AUTH_PLAYER_USERNAME,
        auth_player_password=INSECURE_AUTH_PLAYER_PASSWORD,
        auth_secret="a-long-random-signing-secret",
    )
    try:
        validate_production_secrets(cfg)
    except RuntimeError as exc:
        assert "AUTH_PLAYER_PASSWORD" in str(exc) or "AUTH_PLAYER_USERNAME" in str(exc)
    else:
        raise AssertionError("expected RuntimeError for insecure player credentials")


def test_resolve_media_path_contains_under_root() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "campaigns").mkdir()
        # Patch settings.media_root for this check.
        from app import media as media_mod

        original = media_mod.settings.media_root
        media_mod.settings.media_root = root
        try:
            ok = resolve_media_path("campaigns/abc.jpg")
            assert ok is not None
            assert ok == (root / "campaigns" / "abc.jpg").resolve()

            assert resolve_media_path("../etc/passwd") is None
            assert resolve_media_path("/etc/passwd") is None
            assert resolve_media_path("campaigns/../../outside.txt") is None
        finally:
            media_mod.settings.media_root = original


def test_ai_prompts_npc_and_location() -> None:
    pos, neg = build_prompts(
        "npc",
        {
            "name": "Mira",
            "role_occupation": "dock witch",
            "alignment": "CN",
            "appearance": "salt-stained cloak, green eyes",
            "secret_hook": "serves a drowned god",
        },
        guidance="moonlit pier",
    )
    assert "Mira" in pos
    assert "dock witch" in pos
    assert "moonlit pier" in pos
    assert "blurry" in neg

    loc_pos, loc_neg = build_prompts(
        "location",
        {
            "title": "Sunken Market",
            "description": "Lanterns over tidal stalls",
            "objects": [{"name": "Tide bell", "description": "rings at dusk"}],
            "loot": ["pearl dagger"],
        },
    )
    assert "Sunken Market" in loc_pos
    assert "Tide bell" in loc_pos
    assert "landscape" in loc_pos
    assert "portrait" in loc_neg


def test_comfy_workflow_sizes() -> None:
    workflow = build_workflow("npc", "a hero", "blurry", seed=42)
    assert workflow["3"]["inputs"]["seed"] == 42
    assert workflow["6"]["inputs"]["text"] == "a hero"
    assert workflow["7"]["inputs"]["text"] == "blurry"
    width, height = SIZE_BY_KIND["npc"]
    assert workflow["5"]["inputs"]["width"] == width
    assert workflow["5"]["inputs"]["height"] == height

    landscape = build_workflow("location", "a place", "text", seed=1)
    lw, lh = SIZE_BY_KIND["location"]
    assert landscape["5"]["inputs"]["width"] == lw
    assert landscape["5"]["inputs"]["height"] == lh


def main() -> int:
    test_validate_allows_debug_with_insecure_defaults()
    print("validate_production_secrets DEBUG=true OK")
    test_validate_rejects_insecure_when_not_debug()
    print("validate_production_secrets rejects insecure username OK")
    test_validate_rejects_empty_secret_when_not_debug()
    print("validate_production_secrets rejects empty secret OK")
    test_validate_accepts_strong_secrets_when_not_debug()
    print("validate_production_secrets strong secrets OK")
    test_resolve_media_path_contains_under_root()
    print("resolve_media_path containment OK")
    test_ai_prompts_npc_and_location()
    print("ai_prompts NPC/location OK")
    test_comfy_workflow_sizes()
    print("comfy workflow template OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
