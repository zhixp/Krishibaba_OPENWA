"""
Flash announcement broadcast system.

Admin-only endpoint for queueing targeted messages without invoking AI.
"""
import logging
import re
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.core.security import redacted_identifier, verify_broadcast_admin_key
from app.database.db import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


class BroadcastRequest(BaseModel):
    pincode: Optional[str] = Field("all", max_length=6)
    crop: Optional[str] = Field("all", min_length=1, max_length=80)
    message_text: str = Field(..., min_length=1, max_length=1200)

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value: Optional[str]) -> str:
        normalized = (value or "all").strip()
        if normalized.lower() == "all":
            return "all"
        if not re.fullmatch(r"\d{6}", normalized):
            raise ValueError("pincode must be 'all' or a 6-digit pincode")
        return normalized

    @field_validator("crop")
    @classmethod
    def normalize_crop(cls, value: Optional[str]) -> str:
        return (value or "all").strip() or "all"


@router.post("/send", dependencies=[Depends(verify_broadcast_admin_key)])
async def send_broadcast(request: BroadcastRequest, db: aiosqlite.Connection = Depends(get_db)):
    """
    Queue a flash announcement for targeted farmers.

    Targeting patterns:
    - pincode="464774", crop="all": all farmers in that pincode
    - pincode="all", crop="gehu": all farmers growing that crop
    - pincode="all", crop="all": all farmers
    - pincode="464774", crop="gehu": specific pincode and crop
    """
    try:
        query = "SELECT uid FROM users WHERE 1=1"
        params = []

        if request.pincode and request.pincode.lower() != "all":
            query += " AND default_pincode = ?"
            params.append(request.pincode)

        if request.crop and request.crop.lower() != "all":
            query += " AND crops LIKE ?"
            params.append(f"%{request.crop}%")

        logger.info("Broadcast targeting prepared")

        cursor = await db.execute(query, params)
        target_users = await cursor.fetchall()

        if not target_users:
            logger.info("Broadcast skipped: no matching users")
            return {
                "status": "success",
                "farmers_reached": 0,
                "message": "No users matched the targeting criteria",
            }

        formatted_message = f"Krishi Baba Suchna\n\n{request.message_text.strip()}"
        delivered_count = 0

        for user_row in target_users:
            uid = user_row[0]

            try:
                await db.execute(
                    """INSERT INTO chat_history
                       (user_id, user_message, bot_response, intent, detected_location)
                       VALUES (?, NULL, ?, 'broadcast', NULL)""",
                    (uid, formatted_message),
                )
                await db.execute(
                    """INSERT INTO chat_messages (uid, role, content)
                       VALUES (?, 'assistant', ?)""",
                    (uid, formatted_message),
                )
                delivered_count += 1
            except Exception as exc:
                logger.error(
                    "Broadcast delivery failed for uid_hash=%s: %s",
                    redacted_identifier(uid),
                    exc,
                )

        await db.commit()
        logger.info("Broadcast queued for %s/%s farmers", delivered_count, len(target_users))

        return {
            "status": "success",
            "farmers_reached": delivered_count,
            "targeted": len(target_users),
            "message_length": len(formatted_message),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Broadcast failed: %s", exc)
        raise HTTPException(status_code=500, detail="Broadcast failed") from exc
