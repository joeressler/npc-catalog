"""ComfyUI HTTP client: submit SDXL workflow, wait, fetch PNG bytes."""

from __future__ import annotations

import asyncio
import copy
import json
import random
import time
import uuid
from pathlib import Path
from typing import Any, Literal

import httpx
from fastapi import HTTPException, status

from app.config import settings

ImageKind = Literal["npc", "location"]

WORKFLOW_PATH = Path(__file__).resolve().parent.parent / "workflows" / "sdxl_txt2img.json"

# Portrait vs landscape latent sizes for SDXL.
SIZE_BY_KIND: dict[ImageKind, tuple[int, int]] = {
    "npc": (832, 1216),
    "location": (1216, 832),
}


def _load_workflow_template() -> dict[str, Any]:
    if not WORKFLOW_PATH.is_file():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ComfyUI workflow template is missing.",
        )
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def build_workflow(
    kind: ImageKind,
    positive: str,
    negative: str,
    seed: int | None = None,
) -> dict[str, Any]:
    workflow = copy.deepcopy(_load_workflow_template())
    width, height = SIZE_BY_KIND[kind]
    workflow["5"]["inputs"]["width"] = width
    workflow["5"]["inputs"]["height"] = height
    workflow["6"]["inputs"]["text"] = positive
    workflow["7"]["inputs"]["text"] = negative
    workflow["3"]["inputs"]["seed"] = seed if seed is not None else random.randint(0, 2**32 - 1)
    return workflow


async def comfyui_reachable() -> bool:
    if not settings.comfyui_configured:
        return False
    base = settings.comfyui_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{base}/system_stats")
            return response.status_code < 500
    except httpx.HTTPError:
        return False


async def generate_image_png(
    kind: ImageKind,
    positive: str,
    negative: str,
) -> bytes:
    """Queue a workflow on ComfyUI and return the first output PNG."""
    if not settings.comfyui_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI image generation is not enabled.",
        )

    base = settings.comfyui_url.rstrip("/")
    client_id = uuid.uuid4().hex
    workflow = build_workflow(kind, positive, negative)
    timeout = httpx.Timeout(30.0, read=settings.comfyui_timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            queued = await client.post(
                f"{base}/prompt",
                json={"prompt": workflow, "client_id": client_id},
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ComfyUI is unreachable.",
            ) from exc

        if queued.status_code >= 400:
            detail = queued.text[:300] or "ComfyUI rejected the workflow."
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=detail)

        payload = queued.json()
        prompt_id = payload.get("prompt_id")
        if not prompt_id:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                detail="ComfyUI did not return a prompt_id.",
            )
        if payload.get("node_errors"):
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                detail="ComfyUI workflow has node errors (is SDXL installed?).",
            )

        image_meta = await _wait_for_image(client, base, prompt_id)
        return await _fetch_image(client, base, image_meta)


async def _wait_for_image(
    client: httpx.AsyncClient,
    base: str,
    prompt_id: str,
) -> dict[str, Any]:
    deadline = time.monotonic() + settings.comfyui_timeout_seconds
    while time.monotonic() < deadline:
        try:
            history = await client.get(f"{base}/history/{prompt_id}")
        except httpx.HTTPError as exc:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Lost connection to ComfyUI while waiting.",
            ) from exc

        if history.status_code == 200:
            data = history.json()
            entry = data.get(prompt_id)
            if entry:
                outputs = entry.get("outputs") or {}
                for node_out in outputs.values():
                    images = node_out.get("images") or []
                    if images:
                        return images[0]
                status_block = entry.get("status") or {}
                if status_block.get("status_str") == "error" or status_block.get("completed"):
                    # Completed with no images — treat as failure.
                    if not any((node.get("images") or []) for node in outputs.values()):
                        raise HTTPException(
                            status.HTTP_502_BAD_GATEWAY,
                            detail="ComfyUI finished without an image.",
                        )

        await asyncio.sleep(1.0)

    raise HTTPException(
        status.HTTP_504_GATEWAY_TIMEOUT,
        detail="Timed out waiting for ComfyUI image generation.",
    )


async def _fetch_image(
    client: httpx.AsyncClient,
    base: str,
    image_meta: dict[str, Any],
) -> bytes:
    params = {
        "filename": image_meta.get("filename"),
        "subfolder": image_meta.get("subfolder") or "",
        "type": image_meta.get("type") or "output",
    }
    try:
        response = await client.get(f"{base}/view", params=params)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to download image from ComfyUI.",
        ) from exc

    if response.status_code >= 400 or not response.content:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="ComfyUI image download failed.",
        )
    return response.content
