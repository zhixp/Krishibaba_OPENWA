"""
ASYNC MANDI SCRAPER - Uses existing agmarknet_api.py
NO NEW CODE - Just wiring up what works
"""
import asyncio
import sqlite3
from app.services.agmarknet_api import agmarknet_api
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "krishi_baba.db"

async def populate_mandi_cache():
    """
    Fetch prices from existing API and save to DB
    This runs ASYNC - never during chat
    """
    logger.info("="*70)
    logger.info("🚜 ASYNC MANDI SCRAPER - Using Agmarknet API")
    logger.info("="*70)
    
    # Use YOUR existing superior code
    prices = await agmarknet_api.fetch_state_prices("Madhya Pradesh")
    
    if not prices:
        logger.warning("⚠️ No prices fetched")
        return
    
    logger.info(f"✅ Fetched {len(prices)} prices from API")
    
    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    
    # Clear old data
    conn.execute("DELETE FROM mandi_prices")
    
    # Insert new data
    for price in prices:
        conn.execute("""
            INSERT INTO mandi_prices (
                crop_name, mandi_location, modal_price,
                min_price, max_price, date_scraped
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            price['crop'],
            price['mandi'],
            price['price_modal'],
            price.get('price_min'),
            price.get('price_max'),
            datetime.now().strftime("%Y-%m-%d")
        ))
    
    conn.commit()
    
    # Verify
    count = conn.execute("SELECT COUNT(*) FROM mandi_prices").fetchone()[0]
    conn.close()
    
    logger.info("="*70)
    logger.info(f"✅ CACHE POPULATED: {count} records in DB")
    logger.info("="*70)

if __name__ == "__main__":
    asyncio.run(populate_mandi_cache())
