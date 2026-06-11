"""
Daily Mandi Price Update Script
Run this via cron job to keep database updated with fresh prices
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath('.'))

from app.services.mandi_scraper import mandi_scraper
from app.database.db import get_db
import aiosqlite


async def update_mandi_prices():
    """Scrape and update mandi prices for key crops"""
    
    print("=" * 70)
    print(f"🚜 KRISHI BABA - Daily Mandi Price Update")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # Key crops to scrape daily
    priority_crops = [
        "Wheat", "Paddy", "Soybean", "Gram", "Cotton",
        "Maize", "Mustard", "Groundnut", "Turmeric", "Chili"
    ]
    
    # States to cover
    states = ["Madhya Pradesh", "Uttar Pradesh", "Maharashtra", "Rajasthan"]
    
    total_inserted = 0
    
    # Connect to database
    async for db in get_db():
        for state in states:
            print(f"\n📍 Scraping {state}...")
            
            for crop in priority_crops:
                try:
                    print(f"  🌾 {crop}... ", end='', flush=True)
                    
                    # Scrape prices
                    prices = await mandi_scraper.scrape_crop_prices(
                        crop_name=crop,
                        state_name=state,
                        max_results=10
                    )
                    
                    if not prices:
                        print("No data")
                        continue
                    
                    # Insert into database
                    inserted = 0
                    for price in prices:
                        await db.execute(
                            """INSERT INTO mandi_prices 
                               (crop_name, mandi_location, modal_price, min_price, max_price,
                                date_scraped, state, district)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (price['crop_name'], price['mandi_location'], price['modal_price'],
                             price['min_price'], price['max_price'], price['date_scraped'],
                             price['state'], price['district'])
                        )
                        inserted += 1
                    
                    await db.commit()
                    total_inserted += inserted
                    print(f"✅ {inserted} entries")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                    continue
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
        
        # Cleanup old prices (keep last 30 days)
        print("\n🗑️  Cleaning up old prices...")
        result = await db.execute(
            """DELETE FROM mandi_prices 
               WHERE date_scraped < date('now', '-30 days')"""
        )
        await db.commit()
        print(f"   Deleted old records")
    
    print("\n" + "=" * 70)
    print(f"✅ Update Complete!")
    print(f"   Total new entries: {total_inserted}")
    print(f"   Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


async def main():
    try:
        await update_mandi_prices()
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
