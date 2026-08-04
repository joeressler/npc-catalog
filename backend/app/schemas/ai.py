from typing import Any, Literal

from pydantic import BaseModel, Field


class AiStatusRead(BaseModel):
    enabled: bool
    reachable: bool


class AiGenerateRequest(BaseModel):
    kind: Literal["npc", "location"]
    fields: dict[str, Any] = Field(default_factory=dict)
    guidance: str | None = Field(default=None, max_length=500)


class AiGenerateResponse(BaseModel):
    image_base64: str
    mime_type: str = "image/png"
    prompt_used: str
