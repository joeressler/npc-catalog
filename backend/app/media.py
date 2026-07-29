import uuid
from pathlib import Path
from typing import TypeGuard

from fastapi import HTTPException, status
from PIL import Image
from starlette.datastructures import UploadFile

from app.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def is_upload_file(value: object) -> TypeGuard[UploadFile]:
    """True for multipart uploads from File() or request.form() (Starlette base class)."""
    return isinstance(value, UploadFile) and bool(value.filename)


def ensure_media_root() -> Path:
    root = settings.media_root
    (root / "campaigns").mkdir(parents=True, exist_ok=True)
    (root / "npcs").mkdir(parents=True, exist_ok=True)
    (root / "locations").mkdir(parents=True, exist_ok=True)
    return root


def _save_image(upload: UploadFile, subdirectory: str) -> str:
    """Persist a validated image under subdirectory and return its relative path."""
    if not upload.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Image filename is required.")

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unsupported image format.")

    media_dir = ensure_media_root() / subdirectory
    media_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    destination = media_dir / filename

    try:
        image = Image.open(upload.file)
        image.verify()
        upload.file.seek(0)
        image = Image.open(upload.file)
        image.save(destination)
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
    full_path = settings.media_root / image_path
    if full_path.is_file():
        full_path.unlink()


def build_media_url(_base_url: str, image_path: str | None) -> str | None:
    if not image_path:
        return None
    # Relative path (base_url intentionally unused) so the SPA host/port serves /media via nginx.
    return f"/media/{image_path.lstrip('/')}"
