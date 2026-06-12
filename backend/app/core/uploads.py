"""
Upload validation and bounded file persistence helpers.
"""
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.security import safe_storage_token


ALLOWED_AUDIO_MIME_TYPES = {
    "audio/aac",
    "audio/amr",
    "audio/mp4",
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "audio/x-wav",
    "audio/3gpp",
}
ALLOWED_AUDIO_SUFFIXES = {".aac", ".amr", ".m4a", ".mp3", ".oga", ".ogg", ".opus", ".wav", ".webm", ".3gp"}

ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def _normalized_content_type(upload: UploadFile) -> str:
    return (upload.content_type or "").split(";")[0].strip().lower()


def _validate_upload_type(
    upload: UploadFile,
    allowed_mime_types: Iterable[str],
    allowed_suffixes: Iterable[str],
) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    content_type = _normalized_content_type(upload)

    if content_type not in set(allowed_mime_types) and suffix not in set(allowed_suffixes):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type",
        )

    if suffix not in set(allowed_suffixes):
        suffix = ".bin"

    return suffix


async def save_bounded_upload(
    upload: UploadFile,
    destination_dir: Path,
    owner_id: str,
    allowed_mime_types: Iterable[str],
    allowed_suffixes: Iterable[str],
    max_size_mb: int,
) -> Tuple[str, Path, int]:
    """
    Validate and save an UploadFile without trusting the original filename.

    Returns (stored_filename, stored_path, size_bytes).
    """
    suffix = _validate_upload_type(upload, allowed_mime_types, allowed_suffixes)
    max_bytes = max_size_mb * 1024 * 1024
    destination_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_storage_token(owner_id)}_{timestamp}_{uuid4().hex[:12]}{suffix}"
    root = destination_dir.resolve()
    file_path = (root / filename).resolve()

    try:
        file_path.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid upload path") from exc

    total_bytes = 0
    try:
        with file_path.open("wb") as buffer:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Limit is {max_size_mb} MB",
                    )

                buffer.write(chunk)
    except Exception:
        if file_path.exists():
            file_path.unlink()
        raise

    return filename, file_path, total_bytes


def max_audio_size_mb() -> int:
    return max(1, settings.MAX_AUDIO_SIZE_MB)
