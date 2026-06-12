"""
Ad campaign admin router for keyword-triggered advertisements.
"""
import logging
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, Form, HTTPException

from app.core.security import verify_admin_key
from app.database.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/v1/admin/ads",
    tags=["Ad Admin"],
    dependencies=[Depends(verify_admin_key)],
)


def _normalize_cta_link(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    normalized = value.strip()
    if normalized.startswith(("http://", "https://", "tel:", "mailto:")):
        return normalized

    raise HTTPException(status_code=400, detail="cta_link must be http, https, tel, or mailto")


@router.get("/campaigns")
async def list_campaigns(db: aiosqlite.Connection = Depends(get_db)):
    """Get all ad campaigns."""
    try:
        cursor = await db.execute(
            """
            SELECT id, title, message, keywords, cta, cta_link, icon,
                   active, relevance_threshold, location_filter, created_at
            FROM ad_campaigns
            ORDER BY created_at DESC
            """
        )
        rows = await cursor.fetchall()

        campaigns = [
            {
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
                "created_at": row[10],
            }
            for row in rows
        ]

        return {"success": True, "campaigns": campaigns}

    except Exception as exc:
        logger.error("List campaigns error: %s", exc)
        return {"success": False, "message": "Unable to list campaigns"}


@router.post("/campaigns")
async def create_campaign(
    title: str = Form(..., min_length=1, max_length=120),
    message: str = Form(..., min_length=1, max_length=600),
    keywords: str = Form(..., min_length=1, max_length=400),
    cta: str = Form(..., min_length=1, max_length=80),
    cta_link: Optional[str] = Form(None, max_length=500),
    icon: str = Form("ad", max_length=16),
    relevance_threshold: float = Form(0.5, ge=0, le=1),
    location_filter: Optional[str] = Form(None, max_length=120),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Create a new ad campaign."""
    try:
        cta_link = _normalize_cta_link(cta_link)

        await db.execute(
            """
            INSERT INTO ad_campaigns
            (title, message, keywords, cta, cta_link, icon, relevance_threshold, location_filter, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (title, message, keywords, cta, cta_link, icon, relevance_threshold, location_filter),
        )
        await db.commit()

        return {"success": True, "message": "Campaign created"}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Create campaign error: %s", exc)
        return {"success": False, "message": "Unable to create campaign"}


@router.put("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: int,
    title: Optional[str] = Form(None, max_length=120),
    message: Optional[str] = Form(None, max_length=600),
    keywords: Optional[str] = Form(None, max_length=400),
    active: Optional[bool] = Form(None),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Update a campaign."""
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

        return {"success": True, "message": "Campaign updated"}

    except Exception as exc:
        logger.error("Update campaign error: %s", exc)
        return {"success": False, "message": "Unable to update campaign"}


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """Delete a campaign."""
    try:
        await db.execute("DELETE FROM ad_campaigns WHERE id = ?", (campaign_id,))
        await db.commit()

        return {"success": True, "message": "Campaign deleted"}

    except Exception as exc:
        logger.error("Delete campaign error: %s", exc)
        return {"success": False, "message": "Unable to delete campaign"}


@router.get("/analytics")
async def get_analytics(db: aiosqlite.Connection = Depends(get_db)):
    """Get ad performance analytics."""
    try:
        cursor = await db.execute(
            """
            SELECT c.id, c.title, COUNT(i.id) as impressions,
                   COUNT(DISTINCT i.uid) as unique_users
            FROM ad_campaigns c
            LEFT JOIN ad_impressions i ON c.id = i.campaign_id
            GROUP BY c.id, c.title
            ORDER BY impressions DESC
            """
        )
        rows = await cursor.fetchall()

        analytics = [
            {
                "campaign_id": row[0],
                "title": row[1],
                "impressions": row[2],
                "unique_users": row[3],
            }
            for row in rows
        ]

        return {"success": True, "analytics": analytics}

    except Exception as exc:
        logger.error("Analytics error: %s", exc)
        return {"success": False, "message": "Unable to load analytics"}
