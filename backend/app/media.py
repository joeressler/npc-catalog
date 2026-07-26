import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def ensure_media_root() -> Path:
    root = settings.media_root
    campaigns_dir = root / "campaigns"
    campaigns_dir.mkdir(parents=True, exist_ok=True)
    return campaigns_dir


def save_campaign_image(upload: UploadFile) -> str:
    """Persist a validated campaign image and return its relative storage path."""
    if not upload.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Image filename is required.")

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unsupported image format.")

    campaigns_dir = ensure_media_root()
    filename = f"{uuid.uuid4().hex}{suffix}"
    destination = campaigns_dir / filename

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

    return f"campaigns/{filename}"


def delete_campaign_image(image_path: str | None) -> None:
    if not image_path:
        return
    full_path = settings.media_root / image_path
    if full_path.is_file():
        full_path.unlink()


def build_media_url(base_url: str, image_path: str | None) -> str | None:
    if not image_path:
        return None
    return f"{base_url.rstrip('/')}/media/{image_path.lstrip('/')}"
