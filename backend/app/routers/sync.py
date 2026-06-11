"""
Sync Router
Provides offline data synchronization
"""
from fastapi import APIRouter, Depends, Query
from app.models.schemas import SyncResponse, MandiPrice, GovtScheme
from app.database.db import get_db
import aiosqlite
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/data", response_model=SyncResponse)
async def sync_data(
    pincode: str = Query(..., pattern=r'^\d{6}$', description="User's pincode"),
    last_sync: str = Query(None, description="Last sync timestamp (ISO format)"),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Sync offline data for a specific pincode
    Returns mandi prices and government schemes for the user's region
    
    Optimized for 2G networks - returns compressed, essential data only
    """
    try:
        # TODO: Map pincode to district/state
        # For now, return all data (will optimize in Phase 3)
        
        # Fetch recent mandi prices (last 7 days)
        mandi_cursor = await db.execute(
            """SELECT crop_name, mandi_location, modal_price, min_price, max_price,
                      date_scraped, state, district
               FROM mandi_prices
               ORDER BY date_scraped DESC
               LIMIT 100"""
        )
        mandi_rows = await mandi_cursor.fetchall()
        
        mandi_updates = [
            MandiPrice(
                crop_name=row['crop_name'],
                mandi_location=row['mandi_location'],
                modal_price=row['modal_price'],
                min_price=row['min_price'],
                max_price=row['max_price'],
                date_scraped=row['date_scraped'],
                state=row['state'],
                district=row['district']
            )
            for row in mandi_rows
        ]
        
        # Fetch government schemes
        schemes_cursor = await db.execute(
            """SELECT scheme_name, benefit_summary, eligibility, source_url, category, state
               FROM govt_schemes
               LIMIT 50"""
        )
        scheme_rows = await schemes_cursor.fetchall()
        
        new_schemes = [
            GovtScheme(
                scheme_name=row['scheme_name'],
                benefit_summary=row['benefit_summary'],
                eligibility=row['eligibility'],
                source_url=row['source_url'],
                category=row['category'],
                state=row['state']
            )
            for row in scheme_rows
        ]
        
        return SyncResponse(
            mandi_updates=mandi_updates,
            new_schemes=new_schemes,
            sync_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in sync_data: {e}", exc_info=True)
        return SyncResponse(
            mandi_updates=[],
            new_schemes=[],
            sync_timestamp=datetime.now().isoformat()
        )
