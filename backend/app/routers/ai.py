"""Auth-gated AI image generation proxy for ComfyUI."""

from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.schemas.ai import AiGenerateRequest, AiGenerateResponse, AiStatusRead
from app.services.ai_prompts import build_prompts
from app.services.comfyui import comfyui_reachable, generate_image_png

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status/", response_model=AiStatusRead)
async def ai_status() -> AiStatusRead:
    configured = settings.comfyui_configured
    reachable = await comfyui_reachable() if configured else False
    return AiStatusRead(enabled=configured and reachable, reachable=reachable)


@router.post("/generate-image/", response_model=AiGenerateResponse)
async def generate_image(payload: AiGenerateRequest) -> AiGenerateResponse:
    if not settings.comfyui_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI image generation is not enabled.",
        )
    if not await comfyui_reachable():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ComfyUI is not reachable yet. Try again shortly.",
        )

    positive, negative = build_prompts(payload.kind, payload.fields, payload.guidance)
    if not positive.strip():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Not enough character or location detail to build a prompt.",
        )

    png_bytes = await generate_image_png(payload.kind, positive, negative)
    return AiGenerateResponse(
        image_base64=base64.b64encode(png_bytes).decode("ascii"),
        mime_type="image/png",
        prompt_used=positive,
    )
