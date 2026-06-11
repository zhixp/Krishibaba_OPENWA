"""
Background Scraper Watchdog
Runs scraper and sends alerts on failure
Philosophy: "Serve Stale Data > Serve No Data"
"""
import asyncio
import sys
import os
from datetime import datetime
import traceback

sys.path.insert(0, os.path.abspath('.'))


async def send_alert(message: str, level: str = "ERROR"):
    """
    Send alert (will add Telegram/Email later)
    For now, just log critically
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "="*70)
    print(f"🚨 SCRAPER ALERT [{level}] - {timestamp}")
    print("="*70)
    print(message)
    print("="*70 + "\n")
    
    # TODO: Add Telegram bot notification
    # telegram_bot_send(f"🚨 Krishi Baba Alert:\n{message}")


async def run_scraper():
    """
    Production scraper using NETWORK SNIPER
    Intercepts agmarknet API responses (JSON)
    """
    from app.services.agmarknet_scraper import sniper
    from app.database.db import get_db
    
    print("🎯 KRISHI BABA - Network Sniper Scraper")
    print("Source: agmarknet.gov.in (API intercept)")
    print("Method: Capture JSON responses directly")
    print()
    
    total_inserted = 0
    
    # Run sniper for Madhya Pradesh
    logger.info("🎯 Sniping Madhya Pradesh prices...")
    prices = await sniper.snipe_madhya_pradesh(headless=True)
    
    if prices:
        async for db in get_db():
            for price in prices:
                await db.execute(
                    """INSERT OR IGNORE INTO mandi_price_history
                       (crop, mandi, price_min, price_max, price_modal,
                        source_date, state, district, traded_quantity, arrivals_quantity, arrival_tonnes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (price['crop'], price['mandi'],
                     price['price_min'], price['price_max'], price['price_modal'],
                     price['source_date'], price['state'], price['district'],
                     price.get('traded_quantity'), price.get('arrivals_quantity'),
                     price.get('arrivals_quantity', 0))  # Use arrivals_quantity as arrival_tonnes
                )
                total_inserted += 1
            
            await db.commit()
            print(f"\n✅ Inserted {total_inserted} prices to database")
    else:
        print("\n⚠️  No prices sniped")
    
    return total_inserted
    
    async for db in get_db():
        for state in states:
            print(f"\n{'='*70}")
            print(f"📍 Scraping {state}")
            print(f"{'='*70}")
            
            try:
                # Scrape entire state (all districts)
                all_prices = await agmarknet_production.scrape_state_all_districts(
                    state_name=state,
                    headless=True  # Headless for production
                )
                
                if all_prices:
                    for price in all_prices:
                        await db.execute(
                            """INSERT OR IGNORE INTO mandi_price_history
                               (crop, mandi, price_min, price_max, price_modal,
                                source_date, state, district, traded_quantity, arrivals_quantity)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (price['crop'], price['mandi'],
                             price['price_min'], price['price_max'], price['price_modal'],
                             price['source_date'], price['state'], price['district'],
                             price.get('traded_quantity'), price.get('arrivals_quantity'))
                        )
                        total_inserted += 1
                    
                    await db.commit()
                    print(f"\n✅ {state}: Inserted {len(all_prices)} prices to database")
                else:
                    print(f"\n⚠️  {state}: No data scraped")
                    
            except Exception as e:
                print(f"\n❌ {state} failed completely: {e}")
                await send_alert(f"State scraping failed: {state}\nError: {e}", "ERROR")
                continue
    
    print(f"\n{'='*70}")
    print(f"✅ SCRAPER COMPLETE")
    print(f"Total entries inserted: {total_inserted}")
    print(f"{'='*70}")
    
    return total_inserted


async def watchdog():
    """
    Watchdog wrapper - catches errors and sends alerts
    """
    print("=" * 70)
    print("🚜 KRISHI BABA - Scraper Watchdog")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    try:
        result = await run_scraper()
        
        if result == 0:
            await send_alert(
                "⚠️  Scraper ran but inserted 0 records. Site may be down or empty.",
                level="WARNING"
            )
        else:
            print(f"\n🎉 Success! Inserted {result} records.")
            
    except Exception as e:
        error_msg = f"""
🔥 SCRAPER CRASHED!

Error: {str(e)}

Traceback:
{traceback.format_exc()}

Action: App will serve stale data from database.
Users will see 🟠 orange "old data" warning.
        """
        await send_alert(error_msg, level="CRITICAL")
        
        # DON'T crash the entire system
        # Just log and exit gracefully
        print("\n❌ Scraper failed, but system continues (serving stale data)")
        return 1
    
    return 0


async def main():
    return await watchdog()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
