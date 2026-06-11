"""
Admin Router
Protected endpoints for data ingestion and management
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from app.models.schemas import MandiPrice, GovtScheme
from app.database.db import get_db
from app.core.config import settings
import aiosqlite
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_admin_key(x_api_key: str = Header(...)):
    """Dependency to verify admin API key"""
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@router.post("/ingest/mandi", dependencies=[Depends(verify_admin_key)])
async def ingest_mandi_prices(
    prices: List[MandiPrice],
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Bulk insert mandi prices
    Protected by API key - called by scraper cron job
    """
    try:
        inserted = 0
        for price in prices:
            await db.execute(
                """INSERT INTO mandi_prices 
                   (crop_name, mandi_location, modal_price, min_price, max_price, 
                    date_scraped, state, district)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (price.crop_name, price.mandi_location, price.modal_price,
                 price.min_price, price.max_price, price.date_scraped,
                 price.state, price.district)
            )
            inserted += 1
        
        await db.commit()
        logger.info(f"✅ Inserted {inserted} mandi price records")
        
        return {
            "status": "success",
            "inserted": inserted,
            "message": f"Successfully ingested {inserted} mandi prices"
        }
        
    except Exception as e:
        logger.error(f"Error ingesting mandi prices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to ingest data")


@router.post("/ingest/schemes", dependencies=[Depends(verify_admin_key)])
async def ingest_govt_schemes(
    schemes: List[GovtScheme],
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Bulk insert government schemes
    Protected by API key
    """
    try:
        inserted = 0
        for scheme in schemes:
            # Check if scheme already exists (by name)
            existing = await db.execute(
                "SELECT id FROM govt_schemes WHERE scheme_name = ?",
                (scheme.scheme_name,)
            )
            if await existing.fetchone():
                # Update existing
                await db.execute(
                    """UPDATE govt_schemes 
                       SET benefit_summary = ?, eligibility = ?, source_url = ?,
                           category = ?, state = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE scheme_name = ?""",
                    (scheme.benefit_summary, scheme.eligibility, scheme.source_url,
                     scheme.category, scheme.state, scheme.scheme_name)
                )
            else:
                # Insert new
                await db.execute(
                    """INSERT INTO govt_schemes 
                       (scheme_name, benefit_summary, eligibility, source_url, category, state)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (scheme.scheme_name, scheme.benefit_summary, scheme.eligibility,
                     scheme.source_url, scheme.category, scheme.state)
                )
                inserted += 1
        
        await db.commit()
        logger.info(f"✅ Processed {inserted} government scheme records")
        
        return {
            "status": "success",
            "inserted": inserted,
            "message": f"Successfully processed {inserted} schemes"
        }
        
    except Exception as e:
        logger.error(f"Error ingesting schemes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to ingest data")


@router.post("/reload-prompts", dependencies=[Depends(verify_admin_key)])
async def reload_prompts():
    """
    Hot-reload AI prompts from YAML file
    Useful for testing prompt changes without restarting server
    """
    from app.core.prompt_manager import prompt_manager
    
    try:
        prompt_manager.reload()
        return {
            "status": "success",
            "message": "Prompts reloaded successfully",
            "available_prompts": prompt_manager.list_prompts()
        }
    except Exception as e:
        logger.error(f"Error reloading prompts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reload prompts")
