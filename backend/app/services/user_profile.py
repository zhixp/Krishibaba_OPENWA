"""
User Profile Manager - "The Notebook"
Tracks user facts and builds context for personalized AI responses
"""
import aiosqlite
import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class UserProfileService:
    """Manages user profile and farming context"""
    
    async def get_profile(
        self,
        db: aiosqlite.Connection,
        uid: str
    ) -> Dict[str, any]:
        """Get complete user profile with context"""
        try:
            cursor = await db.execute(
                """SELECT name, crops, default_district, lat, long,
                          crop_summary, location_data
                   FROM users
                   WHERE uid = ?""",
                (uid,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return self._empty_profile()
            
            return {
                "name": row[0] or "भाई",
                "crops": row[1].split(",") if row[1] else [],
                "location": row[2] or "Unknown",
                "lat": row[3],
                "long": row[4],
                "crop_summary": row[5] or "",
                "location_data": json.loads(row[6]) if row[6] else {}
            }
            
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            return self._empty_profile()
    
    async def get_formatted_context(
        self,
        db: aiosqlite.Connection,
        uid: str
    ) -> str:
        """Get user context formatted for AI prompt"""
        profile = await self.get_profile(db, uid)
        
        context_parts = [f"किसान का नाम: {profile['name']}"]
        
        if profile['crops']:
            context_parts.append(f"फसलें: {', '.join(profile['crops'])}")
        
        if profile['location']:
            context_parts.append(f"इलाका: {profile['location']}")
        
        if profile['crop_summary']:
            context_parts.append(f"नोट्स: {profile['crop_summary']}")
        
        return "\n".join(context_parts)
    
    async def update_crop_summary(
        self,
        db: aiosqlite.Connection,
        uid: str,
        new_fact: str
    ):
        """Add a new fact to user's notebook"""
        try:
            profile = await self.get_profile(db, uid)
            current_summary = profile.get('crop_summary', '')
            
            # Append new fact
            if current_summary:
                updated_summary = f"{current_summary}\n- {new_fact}"
            else:
                updated_summary = f"- {new_fact}"
            
            # Keep only last 10 facts (prevent bloat)
            facts = updated_summary.split('\n')
            if len(facts) > 10:
                facts = facts[-10:]
            updated_summary = '\n'.join(facts)
            
            await db.execute(
                "UPDATE users SET crop_summary = ? WHERE uid = ?",
                (updated_summary, uid)
            )
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update summary: {e}")
    
    async def add_crop(
        self,
        db: aiosqlite.Connection,
        uid: str,
        crop: str
    ):
        """Add a crop to user's list"""
        try:
            profile = await self.get_profile(db, uid)
            crops = set(profile['crops'])
            crops.add(crop)
            
            await db.execute(
                "UPDATE users SET crops = ? WHERE uid = ?",
                (','.join(crops), uid)
            )
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to add crop: {e}")
    
    def _empty_profile(self) -> Dict:
        """Return empty profile structure"""
        return {
            "name": "भाई",
            "crops": [],
            "location": "Unknown",
            "lat": None,
            "long": None,
            "crop_summary": "",
            "location_data": {}
        }


# Singleton instance
user_profile = UserProfileService()
