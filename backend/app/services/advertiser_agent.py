"""
Advertiser Agent - "The Sleeping Sniper"
Keyword-triggered ads with cooldown timer and relevance matching
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import aiosqlite

logger = logging.getLogger(__name__)


class AdvertiserAgent:
    """
    Sidecar agent that triggers relevant ads based on keywords
    Runs in parallel with main chat - zero latency impact
    """
    
    def __init__(self):
        self.cooldown_hours = 24  # Don't spam same ad
        
    async def check_for_ads(
        self,
        message: str,
        user_location: str,
        uid: str,
        db: aiosqlite.Connection
    ) -> Optional[Dict]:
        """
        Check if message triggers any ad campaigns
        
        Returns:
            Ad dict if match found and cooldown passed, None otherwise
        """
        try:
            msg_lower = message.lower()
            
            # Get active campaigns
            campaigns = await self._get_active_campaigns(db, user_location)
            
            if not campaigns:
                return None
            
            # Find best match
            best_match = None
            highest_score = 0
            
            for campaign in campaigns:
                score = self._calculate_match_score(msg_lower, campaign)
                
                if score > highest_score and score >= campaign['relevance_threshold']:
                    # Check cooldown
                    if await self._check_cooldown(db, uid, campaign['id']):
                        best_match = campaign
                        highest_score = score
            
            if best_match:
                logger.info(f"📢 Ad triggered: {best_match['title']} (score: {highest_score})")
                
                # Log impression
                await self._log_impression(db, uid, best_match['id'])
                
                return {
                    "id": best_match['id'],
                    "title": best_match['title'],
                    "message": best_match['message'],
                    "cta": best_match['cta'],
                    "cta_link": best_match['cta_link'],
                    "icon": best_match.get('icon', '📢')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Advertiser error: {e}")
            return None
    
    def _calculate_match_score(self, message: str, campaign: Dict) -> float:
        """
        Calculate relevance score (0-1) based on keyword matches
        """
        keywords = campaign['keywords'].split(',')
        matches = sum(1 for kw in keywords if kw.strip().lower() in message)
        
        if matches == 0:
            return 0.0
        
        # Score = (matches / total keywords) with bonus for multiple matches
        score = min(matches / len(keywords) * 1.2, 1.0)
        return score
    
    async def _get_active_campaigns(
        self,
        db: aiosqlite.Connection,
        user_location: str = None
    ) -> List[Dict]:
        """Get active ad campaigns"""
        query = """
            SELECT id, title, message, keywords, cta, cta_link, icon,
                   relevance_threshold, location_filter
            FROM ad_campaigns
            WHERE active = 1
        """
        
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        
        campaigns = []
        for row in rows:
            # Check location filter
            location_filter = row[8]
            if location_filter and user_location:
                if location_filter.lower() not in user_location.lower():
                    continue  # Skip if location doesn't match
            
            campaigns.append({
                "id": row[0],
                "title": row[1],
                "message": row[2],
                "keywords": row[3],
                "cta": row[4],
                "cta_link": row[5],
                "icon": row[6],
                "relevance_threshold": row[7]
            })
        
        return campaigns
    
    async def _check_cooldown(
        self,
        db: aiosqlite.Connection,
        uid: str,
        campaign_id: int
    ) -> bool:
        """Check if cooldown period has passed"""
        query = """
            SELECT created_at FROM ad_impressions
            WHERE uid = ? AND campaign_id = ?
            ORDER BY created_at DESC LIMIT 1
        """
        
        cursor = await db.execute(query, (uid, campaign_id))
        row = await cursor.fetchone()
        
        if not row:
            return True  # Never shown before
        
        last_shown = datetime.fromisoformat(row[0])
        cooldown_end = last_shown + timedelta(hours=self.cooldown_hours)
        
        return datetime.now() >= cooldown_end
    
    async def _log_impression(
        self,
        db: aiosqlite.Connection,
        uid: str,
        campaign_id: int
    ):
        """Log ad impression for analytics"""
        await db.execute("""
            INSERT INTO ad_impressions (uid, campaign_id, created_at)
            VALUES (?, ?, ?)
        """, (uid, campaign_id, datetime.now().isoformat()))
        await db.commit()


# Singleton
advertiser_agent = AdvertiserAgent()
