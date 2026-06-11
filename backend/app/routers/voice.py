"""
Voice Upload Router - Audio File Storage for Dataset Collection
Intercept → Save → Transcribe → Respond
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.database.db import get_db
import aiosqlite
import logging
from datetime import datetime
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

router = APIRouter()

# Voice storage directory
VOICE_STORAGE_DIR = Path("./data/voices")
VOICE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-voice")
async def upload_voice(
    uid: str = Form(...),
    audio: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Phase 2: Voice Vault
    
    1. Intercept: Receive audio file
    2. Save: Store to data/voices/{uid}_{timestamp}.wav
    3. Log: Record in database
    4. Transcribe: Send to Gemini (future step)
    
    Returns: Transcription and AI response
    """
    try:
        # Generate unique filename: {uid}_{timestamp}.wav
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{uid}_{timestamp}.wav"
        file_path = VOICE_STORAGE_DIR / filename
        
        logger.info(f"🎤 Saving voice file: {filename}")
        
        # Save the audio file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        file_size = file_path.stat().st_size
        logger.info(f"✅ Voice file saved: {file_size} bytes")
        
        # Log voice interaction to database
        await db.execute(
            """INSERT INTO voice_logs (user_id, file_path, file_size, created_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
            (uid, str(file_path), file_size)
        )
        await db.commit()
        
        # TODO: Send to Gemini for transcription
        # For now, return success message
        return {
            "status": "success",
            "message": "Voice file saved successfully",
            "filename": filename,
            "file_size": file_size,
            "note": "Transcription coming soon - dataset collection active"
        }
        
    except Exception as e:
        logger.error(f"Error saving voice file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save voice file: {str(e)}")


@router.get("/voice-stats")
async def get_voice_stats(db: aiosqlite.Connection = Depends(get_db)):
    """Get statistics about collected voice data"""
    try:
        # Count total voice files
        cursor = await db.execute("SELECT COUNT(*), SUM(file_size) FROM voice_logs")
        row = await cursor.fetchone()
        
        total_files = row[0] if row else 0
        total_size_bytes = row[1] if row and row[1] else 0
        total_size_mb = round(total_size_bytes / (1024 * 1024), 2)
        
        # Count unique users
        cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM voice_logs")
        unique_users = (await cursor.fetchone())[0]
        
        return {
            "total_voice_files": total_files,
            "total_size_mb": total_size_mb,
            "unique_users": unique_users,
            "storage_path": str(VOICE_STORAGE_DIR)
        }
        
    except Exception as e:
        logger.error(f"Error getting voice stats: {e}")
        return {
            "total_voice_files": 0,
            "total_size_mb": 0,
            "unique_users": 0,
            "error": str(e)
        }
