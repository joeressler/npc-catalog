import uuid
from pathlib import Path
from typing import TypeGuard

from fastapi import HTTPException, status
from PIL import Image
from starlette.datastructures import UploadFile

from app.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
# Match nginx client_max_body_size.
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_IMAGE_DIMENSION = 8192

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def is_upload_file(value: object) -> TypeGuard[UploadFile]:
    """True for multipart uploads from File() or request.form() (Starlette base class)."""
    return isinstance(value, UploadFile) and bool(value.filename)


def ensure_media_root() -> Path:
    root = settings.media_root
    (root / "campaigns").mkdir(parents=True, exist_ok=True)
    (root / "npcs").mkdir(parents=True, exist_ok=True)
    (root / "locations").mkdir(parents=True, exist_ok=True)
    return root


def resolve_media_path(image_path: str) -> Path | None:
    """Return an absolute path under media_root, or None if outside / invalid."""
    if not image_path or image_path.startswith("/") or "\\" in image_path:
        return None
    root = settings.media_root.resolve()
    candidate = (settings.media_root / image_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _save_image(upload: UploadFile, subdirectory: str) -> str:
    """Persist a validated image under subdirectory and return its relative path."""
    if not upload.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Image filename is required.")

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unsupported image format.")

    # Enforce size before decoding (Spool/temp file or in-memory).
    try:
        upload.file.seek(0, 2)
        size = upload.file.tell()
        upload.file.seek(0)
    except OSError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid image file.") from exc
    if size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds maximum upload size.",
        )

    media_dir = ensure_media_root() / subdirectory
    media_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    destination = media_dir / filename

    try:
        image = Image.open(upload.file)
        image.verify()
        upload.file.seek(0)
        image = Image.open(upload.file)
        width, height = image.size
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Image dimensions exceed the allowed maximum.",
            )
        if width * height > MAX_IMAGE_PIXELS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Image pixel count exceeds the allowed maximum.",
            )
        image.save(destination)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid image file.") from exc
    finally:
        upload.file.close()

    return f"{subdirectory}/{filename}"


def save_campaign_image(upload: UploadFile) -> str:
    """Persist a validated campaign image and return its relative storage path."""
    return _save_image(upload, "campaigns")


def delete_campaign_image(image_path: str | None) -> None:
    _delete_image(image_path)


def save_npc_image(upload: UploadFile) -> str:
    """Persist a validated NPC image and return its relative storage path."""
    return _save_image(upload, "npcs")


def delete_npc_image(image_path: str | None) -> None:
    _delete_image(image_path)


def save_location_image(upload: UploadFile) -> str:
    """Persist a validated location image and return its relative storage path."""
    return _save_image(upload, "locations")


def delete_location_image(image_path: str | None) -> None:
    _delete_image(image_path)


def _delete_image(image_path: str | None) -> None:
    if not image_path:
        return
    full_path = resolve_media_path(image_path)
    if full_path is None:
        return
    if full_path.is_file():
        full_path.unlink()


def build_media_url(_base_url: str, image_path: str | None) -> str | None:
    if not image_path:
        return None
    # Relative path (base_url intentionally unused) so the SPA host/port serves /media via nginx.
    return f"/media/{image_path.lstrip('/')}"
