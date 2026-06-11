"""
Quick Database Stats
Shows current state of price history data
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath('.'))

from app.database.db import get_db


async def show_stats():
    """Display database statistics"""
    print("=" * 70)
    print("🚜 KRISHI BABA - Database Statistics")
    print("=" * 70)
    print()
    
    async for db in get_db():
        # Last scrape time
        cursor = await db.execute(
            "SELECT MAX(scraped_at) as last_scrape FROM mandi_price_history"
        )
        row = await cursor.fetchone()
        last_scrape = dict(row)['last_scrape'] if row else None
        
        if last_scrape:
            print(f"📅 Last Updated: {last_scrape}")
        else:
            print("📅 Last Updated: Never (no data yet)")
        print()
        
        # Total records
        cursor = await db.execute("SELECT COUNT(*) FROM mandi_price_history")
        total = (await cursor.fetchone())[0]
        print(f"📊 Total Price Records: {total:,}")
        
        # Unique crops
        cursor = await db.execute("SELECT COUNT(DISTINCT crop) FROM mandi_price_history")
        crops_count = (await cursor.fetchone())[0]
        print(f"🌾 Crops Tracked: {crops_count}")
        
        # Unique mandis
        cursor = await db.execute("SELECT COUNT(DISTINCT mandi) FROM mandi_price_history")
        mandis_count = (await cursor.fetchone())[0]
        print(f"📍 Mandis Tracked: {mandis_count}")
        
        # Date range
        cursor = await db.execute("SELECT MIN(source_date), MAX(source_date) FROM mandi_price_history")
        date_range = await cursor.fetchone()
        if date_range[0]:
            print(f"📆 Date Range: {date_range[0]} to {date_range[1]}")
            
            # Calculate days of history
            from_date = datetime.strptime(date_range[0], "%Y-%m-%d")
            to_date = datetime.strptime(date_range[1], "%Y-%m-%d")
            days = (to_date - from_date).days + 1
            print(f"   ({days} days of historical data)")
        
        print()
        print("-" * 70)
        print("Top 5 Crops by Data Points:")
        print("-" * 70)
        
        cursor = await db.execute("""
            SELECT crop, COUNT(*) as count
            FROM mandi_price_history
            GROUP BY crop
            ORDER BY count DESC
            LIMIT 5
        """)
        
        top_crops = await cursor.fetchall()
        for i, (crop, count) in enumerate(top_crops, 1):
            print(f"  {i}. {crop}: {count:,} records")
        
        print()
        print("-" * 70)
        print("Recent Price Updates (Last 5):")
        print("-" * 70)
        
        cursor = await db.execute("""
            SELECT crop, mandi, price_modal, source_date
            FROM mandi_price_history
            ORDER BY scraped_at DESC
            LIMIT 5
        """)
        
        recent = await cursor.fetchall()
        for crop, mandi, price, date in recent:
            print(f"  • {crop} @ {mandi}: ₹{price} ({date})")
        
        print()
        print("=" * 70)
        
        # Data freshness warning
        if last_scrape:
            last_scrape_time = datetime.fromisoformat(last_scrape)
            hours_old = (datetime.now() - last_scrape_time).total_seconds() / 3600
            
            if hours_old > 48:
                print("⚠️  WARNING: Data is more than 48 hours old!")
                print("   Consider running: python scripts/watchdog.py")
            elif hours_old > 24:
                print("🟡 Data is getting old (> 24 hours)")
                print("   Scraper should run daily")
            else:
                print("✅ Data is fresh! (< 24 hours old)")
        else:
            print("❌ No data yet! Run: python scripts/watchdog.py")
        
        print("=" * 70)


async def main():
    await show_stats()


if __name__ == "__main__":
    asyncio.run(main())
