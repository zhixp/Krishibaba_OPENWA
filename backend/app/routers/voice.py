"""
Voice upload router for consented dataset collection.
"""
import logging
from pathlib import Path
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.security import redacted_identifier, verify_admin_key
from app.core.uploads import (
    ALLOWED_AUDIO_MIME_TYPES,
    ALLOWED_AUDIO_SUFFIXES,
    max_audio_size_mb,
    save_bounded_upload,
)
from app.database.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

VOICE_STORAGE_DIR = Path("./data/voices")


@router.post("/upload-voice")
async def upload_voice(
    uid: str = Form(...),
    audio: UploadFile = File(...),
    consent_granted: bool = Form(False),
    dialect_guess: Optional[str] = Form(None),
    location_hint: Optional[str] = Form(None),
    crop_hint: Optional[str] = Form(None),
    intent: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Store a consented farmer audio clip for transcription and dataset building.
    """
    file_path: Optional[Path] = None
    try:
        if not consent_granted:
            raise HTTPException(status_code=400, detail="Voice storage requires explicit consent")

        _filename, file_path, file_size = await save_bounded_upload(
            upload=audio,
            destination_dir=VOICE_STORAGE_DIR,
            owner_id=uid,
            allowed_mime_types=ALLOWED_AUDIO_MIME_TYPES,
            allowed_suffixes=ALLOWED_AUDIO_SUFFIXES,
            max_size_mb=max_audio_size_mb(),
        )

        logger.info(
            "Voice file saved for uid_hash=%s bytes=%s",
            redacted_identifier(uid),
            file_size,
        )

        cursor = await db.execute(
            """INSERT INTO voice_logs
               (user_id, file_path, file_size, consent_granted, dialect_guess,
                location_hint, crop_hint, intent, created_at)
               VALUES (?, ?, ?, 1, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (uid, str(file_path), file_size, dialect_guess, location_hint, crop_hint, intent),
        )
        await db.commit()

        return {
            "status": "success",
            "message": "Voice file saved successfully",
            "voice_log_id": cursor.lastrowid,
            "file_size": file_size,
            "note": "Transcription coming soon - dataset collection active",
        }

    except HTTPException:
        if file_path and file_path.exists():
            file_path.unlink()
        raise
    except Exception as exc:
        if file_path and file_path.exists():
            file_path.unlink()
        logger.error("Error saving voice file: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save voice file") from exc


@router.get("/voice-stats", dependencies=[Depends(verify_admin_key)])
async def get_voice_stats(db: aiosqlite.Connection = Depends(get_db)):
    """Return aggregate voice dataset stats for admins."""
    try:
        cursor = await db.execute(
            """SELECT COUNT(*), SUM(file_size),
                      SUM(CASE WHEN consent_granted = 1 THEN 1 ELSE 0 END)
               FROM voice_logs"""
        )
        row = await cursor.fetchone()

        total_files = row[0] if row else 0
        total_size_bytes = row[1] if row and row[1] else 0
        consented_files = row[2] if row and row[2] else 0
        total_size_mb = round(total_size_bytes / (1024 * 1024), 2)

        cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM voice_logs")
        unique_users = (await cursor.fetchone())[0]

        return {
            "total_voice_files": total_files,
            "consented_voice_files": consented_files,
            "total_size_mb": total_size_mb,
            "unique_users": unique_users,
        }

    except Exception as exc:
        logger.error("Error getting voice stats: %s", exc)
        return {
            "total_voice_files": 0,
            "consented_voice_files": 0,
            "total_size_mb": 0,
            "unique_users": 0,
            "error": "Unable to load voice stats",
        }
