from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import ALIGNMENT_CODES_DISPLAY, VALID_ALIGNMENTS
from app.schemas.location import CatalogLocationRead


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AliasRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class NPCWrite(BaseModel):
    campaign: int | None = None
    name: str = Field(max_length=200)
    role_occupation: str = Field(max_length=200)
    alignment: str = Field(max_length=2)
    location: str = Field(default="", max_length=200)
    location_id: int | None = None
    faction: str = ""
    attitude: str = Field(max_length=200)
    party_relationship: str = Field(max_length=200)
    appearance: str = ""
    voice_mannerisms: str = ""
    personality_traits: str = ""
    motivation_goal: str = ""
    secret_hook: str = ""
    knowledge: str = ""
    inventory: str = ""
    dm_notes: str = ""
    session_log: str = ""
    player_visible: bool = False
    aliases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("alignment")
    @classmethod
    def validate_alignment(cls, value: str) -> str:
        if value not in VALID_ALIGNMENTS:
            raise ValueError("Invalid alignment code.")
        return value


class NPCWritePartial(BaseModel):
    campaign: int | None = None
    name: str | None = Field(default=None, max_length=200)
    role_occupation: str | None = Field(default=None, max_length=200)
    alignment: str | None = Field(default=None, max_length=2)
    location: str | None = Field(default=None, max_length=200)
    location_id: int | None = None
    faction: str | None = None
    attitude: str | None = Field(default=None, max_length=200)
    party_relationship: str | None = Field(default=None, max_length=200)
    appearance: str | None = None
    voice_mannerisms: str | None = None
    personality_traits: str | None = None
    motivation_goal: str | None = None
    secret_hook: str | None = None
    knowledge: str | None = None
    inventory: str | None = None
    dm_notes: str | None = None
    session_log: str | None = None
    player_visible: bool | None = None
    aliases: list[str] | None = None
    tags: list[str] | None = None

    @field_validator("alignment")
    @classmethod
    def validate_alignment(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_ALIGNMENTS:
            raise ValueError("Invalid alignment code.")
        return value


class NPCImportItem(BaseModel):
    """Single character in a bulk import. Extra keys are errors so typos surface."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=200)
    role_occupation: str = Field(max_length=200)
    alignment: str = Field(max_length=2)
    location: str = Field(default="", max_length=200)
    location_id: int | None = None
    faction: str = ""
    attitude: str = Field(max_length=200)
    party_relationship: str = Field(max_length=200)
    appearance: str = ""
    voice_mannerisms: str = ""
    personality_traits: str = ""
    motivation_goal: str = ""
    secret_hook: str = ""
    knowledge: str = ""
    inventory: str = ""
    dm_notes: str = ""
    session_log: str = ""
    player_visible: bool = False
    aliases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("name", "role_occupation", "attitude", "party_relationship", mode="before")
    @classmethod
    def required_stripped_string(cls, value: Any) -> str:
        if value is None:
            raise ValueError("This field is required.")
        if not isinstance(value, str):
            raise ValueError("Must be a string.")
        text = value.strip()
        if not text:
            raise ValueError("This field is required.")
        return text

    @field_validator("alignment", mode="before")
    @classmethod
    def validate_alignment(cls, value: Any) -> str:
        if value is None:
            raise ValueError("This field is required.")
        if not isinstance(value, str):
            raise ValueError("Must be a string.")
        code = value.strip()
        if code not in VALID_ALIGNMENTS:
            raise ValueError(
                f"Invalid alignment code. Use one of: {ALIGNMENT_CODES_DISPLAY}."
            )
        return code


class NPCImportFieldError(BaseModel):
    field: str | None = None
    message: str


class NPCImportCreated(BaseModel):
    id: int
    name: str
    index: int


class NPCImportFailed(BaseModel):
    index: int
    name: str | None = None
    errors: list[NPCImportFieldError]


class NPCImportResult(BaseModel):
    created_count: int
    failed_count: int
    created: list[NPCImportCreated]
    failed: list[NPCImportFailed]


def _field_from_loc(loc: tuple[Any, ...]) -> str | None:
    parts = [part for part in loc if part != "body"]
    if not parts:
        return None
    result = str(parts[0])
    for part in parts[1:]:
        if isinstance(part, int) or (isinstance(part, str) and part.isdigit()):
            result += f"[{part}]"
        else:
            result += f".{part}"
    return result


def format_import_field_errors(errors: list[Any]) -> list[NPCImportFieldError]:
    formatted: list[NPCImportFieldError] = []
    for err in errors:
        loc = tuple(err.get("loc") or ())
        err_type = err.get("type", "")
        msg = str(err.get("msg") or "Invalid value.")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        if err_type == "missing":
            msg = "This field is required."
        elif err_type == "extra_forbidden":
            msg = "Unknown field."
        elif err_type == "string_too_long":
            max_length = (err.get("ctx") or {}).get("max_length")
            if max_length:
                msg = f"Must be at most {max_length} characters."
        formatted.append(NPCImportFieldError(field=_field_from_loc(loc), message=msg))
    return formatted


class NPCListRead(BaseModel):
    id: int
    campaign: int
    name: str
    role_occupation: str
    alignment: str
    alignment_display: str
    location: str
    catalog_location: CatalogLocationRead | None = None
    faction: str
    attitude: str
    party_relationship: str
    image: str | None = None
    player_visible: bool = False
    aliases: list[AliasRead]
    tags: list[TagRead]
    created_at: datetime
    updated_at: datetime


class NPCDetailRead(NPCListRead):
    appearance: str
    voice_mannerisms: str
    personality_traits: str
    motivation_goal: str
    secret_hook: str
    knowledge: str
    inventory: str
    dm_notes: str
    session_log: str


def dump_partial(payload: NPCWritePartial) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True)
