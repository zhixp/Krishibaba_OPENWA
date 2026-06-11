"""
Flash Announcement Broadcast System
Sends mass messages to farmers without AI involvement
Admin-only, targets by pincode/crop
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from app.database.db import get_db
from app.core.config import settings
import aiosqlite

router = APIRouter()  # No prefix here, main.py adds /v1/broadcast
logger = logging.getLogger(__name__)

class BroadcastRequest(BaseModel):
    admin_key: str
    pincode: Optional[str] = "all"  # "all" or specific pincode
    crop: Optional[str] = "all"     # "all" or specific crop
    message_text: str

def verify_admin(admin_key: str):
    """Verify admin authentication"""
    if admin_key != settings.BROADCAST_ADMIN_KEY:
        logger.warning(f"Invalid admin key attempt: {admin_key[:10]}...")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin key")
    return True

@router.post("/send")
async def send_broadcast(request: BroadcastRequest, db: aiosqlite.Connection = Depends(get_db)):
    """
    Send flash announcement to targeted farmers
    
    Targeting patterns:
    - pincode="464774", crop="all" → All farmers in that pincode
    - pincode="all", crop="gehu" → All farmers growing that crop
    - pincode="all", crop="all" → ALL farmers (broadcast to everyone)
    - pincode="464774", crop="gehu" → Specific pincode + crop
    """
    try:
        # 1. VERIFY ADMIN
        verify_admin(request.admin_key)
        
        # 2. BUILD QUERY BASED ON TARGETING
        query = "SELECT uid FROM users WHERE 1=1"
        params = []
        
        # Add pincode filter
        if request.pincode and request.pincode.lower() != "all":
            query += " AND default_pincode = ?"
            params.append(request.pincode)
        
        # Add crop filter  
        if request.crop and request.crop.lower() != "all":
            query += " AND crops LIKE ?"
            params.append(f"%{request.crop}%")
        
        logger.info(f"📢 Broadcast Query: {query} | Params: {params}")
        
        # 3. FETCH TARGET USERS
        cursor = await db.execute(query, params)
        target_users = await cursor.fetchall()
        
        if not target_users:
            logger.warning("⚠️ No users found matching criteria")
            return {
                "status": "success",
                "farmers_reached": 0,
                "message": "No users matched the targeting criteria"
            }
        
        # 4. FORMAT MESSAGE
        formatted_message = f"📢 **सरपंच सूचना**\n\n{request.message_text}"
        
        # 5. DELIVER TO EACH USER (Log to chat history)
        delivered_count = 0
        
        for user_row in target_users:
            uid = user_row[0]
            
            try:
                # Insert into chat_history table
                await db.execute(
                    """INSERT INTO chat_history 
                       (user_id, role, message, timestamp) 
                       VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                    (uid, "model", formatted_message)
                )
                delivered_count += 1
                
            except Exception as e:
                logger.error(f"Failed to deliver to {uid}: {e}")
                continue
        
        await db.commit()
        
        # 6. RETURN STATISTICS
        logger.info(f"✅ Broadcast delivered to {delivered_count}/{len(target_users)} farmers")
        
        return {
            "status": "success",
            "farmers_reached": delivered_count,
            "targeted": len(target_users),
            "message_preview": formatted_message[:100] + "..." if len(formatted_message) > 100 else formatted_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Broadcast failed: {e}")
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")
