"""
Chat Memory Service - 20 Message Sliding Window
Stores and retrieves conversation history for context
"""
import aiosqlite
from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChatMemoryService:
    """Manages conversation history for AI context"""
    
    async def save_message(
        self,
        db: aiosqlite.Connection,
        uid: str,
        role: str,  # "user" or "assistant"
        content: str
    ):
        """Save a single message to history"""
        try:
            await db.execute(
                """INSERT INTO chat_messages (uid, role, content, timestamp)
                   VALUES (?, ?, ?, ?)""",
                (uid, role, content, datetime.now().isoformat())
            )
            await db.commit()
            
            # Cleanup: Keep only last 20 messages per user
            await self._cleanup_old_messages(db, uid)
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
    
    async def get_history(
        self,
        db: aiosqlite.Connection,
        uid: str,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """Get last N messages for a user"""
        try:
            cursor = await db.execute(
                """SELECT role, content, timestamp
                   FROM chat_messages
                   WHERE uid = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (uid, limit)
            )
            rows = await cursor.fetchall()
            
            # Reverse to get chronological order
            messages = [
                {
                    "role": row[0],
                    "content": row[1],
                    "timestamp": row[2]
                }
                for row in reversed(rows)
            ]
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []
    
    async def get_formatted_history(
        self,
        db: aiosqlite.Connection,
        uid: str,
        limit: int = 20
    ) -> str:
        """Get history formatted for AI prompt injection"""
        history = await self.get_history(db, uid, limit)
        
        if not history:
            return "यह पहली बार बात हो रही है।"
        
        formatted = ["पिछली बातचीत:"]
        for msg in history:
            role_hindi = "किसान" if msg["role"] == "user" else "आप"
            formatted.append(f"{role_hindi}: {msg['content']}")
        
        return "\n".join(formatted)
    
    async def _cleanup_old_messages(
        self,
        db: aiosqlite.Connection,
        uid: str,
        keep_last: int = 20
    ):
        """Delete messages beyond the limit"""
        try:
            await db.execute(
                """DELETE FROM chat_messages
                   WHERE uid = ?
                   AND id NOT IN (
                       SELECT id FROM chat_messages
                       WHERE uid = ?
                       ORDER BY timestamp DESC
                       LIMIT ?
                   )""",
                (uid, uid, keep_last)
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def clear_history(
        self,
        db: aiosqlite.Connection,
        uid: str
    ):
        """Clear all history for a user (optional feature)"""
        await db.execute("DELETE FROM chat_messages WHERE uid = ?", (uid,))
        await db.commit()


# Singleton instance
chat_memory = ChatMemoryService()
