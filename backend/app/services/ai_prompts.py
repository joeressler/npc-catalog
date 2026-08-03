"""Build DnD-style positive/negative prompts from NPC or location form fields."""

from __future__ import annotations

import re
from typing import Any, Literal

ImageKind = Literal["npc", "location"]

_MARKDOWN_NOISE = re.compile(r"[*_`#>\[\]\(\)!\\|]+")
_WHITESPACE = re.compile(r"\s+")

ALIGNMENT_LABELS = {
    "LG": "lawful good",
    "NG": "neutral good",
    "CG": "chaotic good",
    "LN": "lawful neutral",
    "N": "true neutral",
    "CN": "chaotic neutral",
    "LE": "lawful evil",
    "NE": "neutral evil",
    "CE": "chaotic evil",
}

NPC_NEGATIVE = (
    "blurry, low quality, deformed, extra limbs, bad anatomy, text, watermark, "
    "logo, modern clothing, photograph, selfie, comic panel, split image"
)
LOCATION_NEGATIVE = (
    "blurry, low quality, text, watermark, logo, people close-up, portrait, "
    "modern city, photograph, UI, map icons, split image"
)


def _clean(value: Any, max_len: int = 400) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        parts = [_clean(item, max_len=120) for item in value]
        text = ", ".join(part for part in parts if part)
    else:
        text = str(value).strip()
    if not text:
        return ""
    text = _MARKDOWN_NOISE.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text


def _join_clauses(clauses: list[str]) -> str:
    return ", ".join(clause for clause in clauses if clause)


def build_prompts(
    kind: ImageKind,
    fields: dict[str, Any],
    guidance: str | None = None,
) -> tuple[str, str]:
    """Return (positive_prompt, negative_prompt)."""
    guide = _clean(guidance, max_len=300)
    if kind == "npc":
        positive = _npc_positive(fields, guide)
        negative = NPC_NEGATIVE
    else:
        positive = _location_positive(fields, guide)
        negative = LOCATION_NEGATIVE
    return positive, negative


def _npc_positive(fields: dict[str, Any], guidance: str) -> str:
    name = _clean(fields.get("name"), 80)
    aliases = _clean(fields.get("aliases"), 120)
    role = _clean(fields.get("role_occupation") or fields.get("role"), 120)
    alignment_code = _clean(fields.get("alignment"), 8).upper()
    alignment = ALIGNMENT_LABELS.get(alignment_code, _clean(fields.get("alignment"), 40))
    location = _clean(fields.get("location"), 120)
    faction = _clean(fields.get("faction"), 80)
    attitude = _clean(fields.get("attitude"), 80)
    party_rel = _clean(fields.get("party_relationship"), 80)
    tags = _clean(fields.get("tags"), 160)
    appearance = _clean(fields.get("appearance"), 500)
    voice = _clean(fields.get("voice_mannerisms"), 200)
    personality = _clean(fields.get("personality_traits"), 240)
    motivation = _clean(fields.get("motivation_goal"), 200)
    secret = _clean(fields.get("secret_hook"), 200)
    inventory = _clean(fields.get("inventory"), 160)

    subject = name or "a fantasy character"
    clauses = [
        "Dungeons and Dragons fantasy character portrait",
        "painted illustration",
        "bust half-body",
        "dramatic lighting",
        "detailed face",
        f"named {subject}" if name else subject,
        f"also known as {aliases}" if aliases else "",
        f"occupation {role}" if role else "",
        f"{alignment} alignment" if alignment else "",
        f"from {location}" if location else "",
        f"faction {faction}" if faction else "",
        f"attitude {attitude}" if attitude else "",
        f"party relationship {party_rel}" if party_rel else "",
        f"appearance: {appearance}" if appearance else "",
        f"mannerisms: {voice}" if voice else "",
        f"personality: {personality}" if personality else "",
        f"motivation: {motivation}" if motivation else "",
        f"hidden aspect: {secret}" if secret else "",
        f"carrying: {inventory}" if inventory else "",
        f"keywords: {tags}" if tags else "",
        f"artist direction: {guidance}" if guidance else "",
    ]
    return _join_clauses(clauses)


def _location_positive(fields: dict[str, Any], guidance: str) -> str:
    title = _clean(fields.get("title") or fields.get("name"), 120)
    description = _clean(fields.get("description"), 700)
    objects = fields.get("objects") or []
    loot = fields.get("loot") or []

    object_bits: list[str] = []
    if isinstance(objects, list):
        for obj in objects[:8]:
            if isinstance(obj, dict):
                name = _clean(obj.get("name"), 60)
                desc = _clean(obj.get("description"), 120)
                if name and desc:
                    object_bits.append(f"{name} ({desc})")
                elif name:
                    object_bits.append(name)
            else:
                bit = _clean(obj, 80)
                if bit:
                    object_bits.append(bit)

    loot_bits: list[str] = []
    if isinstance(loot, list):
        for item in loot[:6]:
            if isinstance(item, dict):
                bit = _clean(item.get("description") or item.get("name"), 80)
            else:
                bit = _clean(item, 80)
            if bit:
                loot_bits.append(bit)

    place = title or "a fantasy location"
    clauses = [
        "Dungeons and Dragons fantasy landscape",
        "establishing shot of a location",
        "painted illustration",
        "atmospheric environment art",
        "no large readable text",
        place,
        f"description: {description}" if description else "",
        f"notable features: {', '.join(object_bits)}" if object_bits else "",
        f"loot atmosphere: {', '.join(loot_bits)}" if loot_bits else "",
        f"artist direction: {guidance}" if guidance else "",
    ]
    return _join_clauses(clauses)
