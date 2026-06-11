"""
Ad Campaign Admin Router
Manage keyword-triggered advertisements
"""
from fastapi import APIRouter, Depends, Form
from app.database.db import get_db
import aiosqlite
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/admin/ads", tags=["Ad Admin"])


@router.get("/campaigns")
async def list_campaigns(db: aiosqlite.Connection = Depends(get_db)):
    """Get all ad campaigns"""
    try:
        cursor = await db.execute("""
            SELECT id, title, message, keywords, cta, cta_link, icon,
                   active, relevance_threshold, location_filter, created_at
            FROM ad_campaigns
            ORDER BY created_at DESC
        """)
        rows = await cursor.fetchall()
        
        campaigns = [{
            "id": row[0],
            "title": row[1],
            "message": row[2],
            "keywords": row[3],
            "cta": row[4],
            "cta_link": row[5],
            "icon": row[6],
            "active": bool(row[7]),
            "relevance_threshold": row[8],
            "location_filter": row[9],
            "created_at": row[10]
        } for row in rows]
        
        return {"success": True, "campaigns": campaigns}
        
    except Exception as e:
        logger.error(f"List campaigns error: {e}")
        return {"success": False, "message": str(e)}


@router.post("/campaigns")
async def create_campaign(
    title: str = Form(...),
    message: str = Form(...),
    keywords: str = Form(...),  # Comma-separated
    cta: str = Form(...),
    cta_link: str = Form(None),
    icon: str = Form("📢"),
    relevance_threshold: float = Form(0.5),
    location_filter: str = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Create new ad campaign"""
    try:
        await db.execute("""
            INSERT INTO ad_campaigns 
            (title, message, keywords, cta, cta_link, icon, relevance_threshold, location_filter, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (title, message, keywords, cta, cta_link, icon, relevance_threshold, location_filter))
        
        await db.commit()
        
        return {"success": True, "message": "Campaign created!"}
        
    except Exception as e:
        logger.error(f"Create campaign error: {e}")
        return {"success": False, "message": str(e)}


@router.put("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: int,
    title: str = Form(None),
    message: str = Form(None),
    keywords: str = Form(None),
    active: bool = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Update campaign"""
    try:
        updates = []
        params = []
        
        if title: 
            updates.append("title = ?")
            params.append(title)
        if message:
            updates.append("message = ?")
            params.append(message)
        if keywords:
            updates.append("keywords = ?")
            params.append(keywords)
        if active is not None:
            updates.append("active = ?")
            params.append(1 if active else 0)
        
        if not updates:
            return {"success": False, "message": "No updates provided"}
        
        params.append(campaign_id)
        query = f"UPDATE ad_campaigns SET {', '.join(updates)} WHERE id = ?"
        
        await db.execute(query, params)
        await db.commit()
        
        return {"success": True, "message": "Campaign updated!"}
        
    except Exception as e:
        logger.error(f"Update campaign error: {e}")
        return {"success": False, "message": str(e)}


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Delete campaign"""
    try:
        await db.execute("DELETE FROM ad_campaigns WHERE id = ?", (campaign_id,))
        await db.commit()
        
        return {"success": True, "message": "Campaign deleted!"}
        
    except Exception as e:
        logger.error(f"Delete campaign error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/analytics")
async def get_analytics(db: aiosqlite.Connection = Depends(get_db)):
    """Get ad performance analytics"""
    try:
        # Total impressions per campaign
        cursor = await db.execute("""
            SELECT c.id, c.title, COUNT(i.id) as impressions,
                   COUNT(DISTINCT i.uid) as unique_users
            FROM ad_campaigns c
            LEFT JOIN ad_impressions i ON c.id = i.campaign_id
            GROUP BY c.id, c.title
            ORDER BY impressions DESC
        """)
        rows = await cursor.fetchall()
        
        analytics = [{
            "campaign_id": row[0],
            "title": row[1],
            "impressions": row[2],
            "unique_users": row[3]
        } for row in rows]
        
        return {"success": True, "analytics": analytics}
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {"success": False, "message": str(e)}
