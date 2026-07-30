"""Unit checks for production hardening helpers (no server required)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.config import (
    INSECURE_AUTH_PASSWORD,
    INSECURE_AUTH_SECRET,
    INSECURE_AUTH_USERNAME,
    Settings,
    validate_production_secrets,
)
from app.media import resolve_media_path


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
        auth_secret="a-long-random-signing-secret",
    )
    validate_production_secrets(cfg)


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
