"""
AGMARKNET SNIPER - Network Intercept Mode
Intercepts API responses instead of parsing HTML
Includes "Unclick Protocol" to avoid server timeouts
"""
from playwright.async_api import async_playwright, Page, Response
from typing import List, Dict, Optional
from datetime import datetime
import logging
import json
import asyncio
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgmarknetSniper:
    """
    Network intercept scraper for agmarknet.gov.in
    Gets clean JSON data instead of parsing HTML
    """
    
    def __init__(self):
        self.url = "https://agmarknet.gov.in/PriceTrends/PriceArrivalTrend.aspx"
        self.captured_data = []
    
    async def snipe_madhya_pradesh(
        self,
        headless: bool = False  # Visible to debug
    ) -> List[Dict]:
        """
        Snipe Madhya Pradesh prices using network intercept
        
        Returns:
            List of price dictionaries from API responses
        """
        logger.info("🎯 AGMARKNET SNIPER - Network Intercept Mode")
        logger.info(f"Target: {self.url}")
        logger.info("Protocol: Unclick 'Select All', snipe MP districts")
        
        all_prices = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless, slow_mo=500)
                page = await browser.new_page()
                page.set_default_timeout(60000)
                
                # Set up response interceptor
                async def handle_response(response: Response):
                    """Intercept API responses containing price data"""
                    try:
                        url = response.url
                        
                        # Look for API endpoint with price data
                        if "price" in url.lower() or "arrival" in url.lower() or "market" in url.lower():
                            if response.status == 200:
                                try:
                                    data = await response.json()
                                    if data and isinstance(data, dict):
                                        logger.info(f"🎯 INTERCEPTED: {url}")
                                        logger.info(f"📦 Data keys: {list(data.keys())}")
                                        self.captured_data.append(data)
                                except:
                                    # Not JSON, skip
                                    pass
                    except Exception as e:
                        pass
                
                # Register interceptor
                page.on("response", handle_response)
                
                # STEP 1: Load page
                logger.info("📍 Loading Price Trends page...")
                await page.goto(self.url, wait_until="networkidle")
                await self._human_delay(2, 3)
                logger.info("✅ Page loaded")
                
                # Screenshot
                await page.screenshot(path="logs/sniper_loaded.png")
                
                # STEP 2: UNCLICK PROTOCOL - State
                logger.info("\n🎯 UNCLICK PROTOCOL: State Selection")
                logger.info("Step 1: Uncheck 'Select All' for States")
                
                # Find state dropdown/multiselect
                # Try to find the container with checkboxes
                try:
                    # Click state dropdown to open
                    state_dropdown = page.locator("text=State").first
                    if await state_dropdown.count() > 0:
                        await state_dropdown.click()
                        await self._human_delay(0.5, 1.0)
                        logger.info("  ✅ State dropdown opened")
                    
                    # Uncheck "Select All"
                    select_all_state = page.locator("text=Select All").first
                    if await select_all_state.count() > 0:
                        await select_all_state.click()
                        await self._human_delay(0.5, 1.0)
                        logger.info("  ✅ Unchecked 'Select All'")
                    
                    # Check only "Madhya Pradesh"
                    mp_checkbox = page.locator("text=Madhya Pradesh").first
                    if await mp_checkbox.count() > 0:
                        await mp_checkbox.click()
                        await self._human_delay(1.0, 1.5)
                        logger.info("  ✅ Selected 'Madhya Pradesh'")
                        await page.wait_for_load_state("networkidle")
                    else:
                        logger.error("  ❌ Could not find Madhya Pradesh checkbox")
                        
                except Exception as e:
                    logger.error(f"  ❌ State selection failed: {e}")
                
                # Screenshot after state selection
                await page.screenshot(path="logs/sniper_state_selected.png")
                
                # STEP 3: UNCLICK PROTOCOL - District
                logger.info("\n🎯 UNCLICK PROTOCOL: District Selection")
                
                try:
                    # Click district dropdown
                    district_dropdown = page.locator("text=District").first
                    if await district_dropdown.count() > 0:
                        await district_dropdown.click()
                        await self._human_delay(0.5, 1.0)
                        logger.info("  ✅ District dropdown opened")
                    
                    # Uncheck "Select All"
                    select_all_district = page.locator("text=Select All").nth(1)  # Second "Select All"
                    if await select_all_district.count() > 0:
                        await select_all_district.click()
                        await self._human_delay(0.5, 1.0)
                        logger.info("  ✅ Unchecked 'Select All' for districts")
                    
                    # Get list of districts (first few for testing)
                    # Try to find district checkboxes
                    district_labels = page.locator("label:near(:text('District'))").all()
                    
                    # For now, select first district (Raisen as example)
                    raisen = page.locator("text=Raisen").first
                    if await raisen.count() > 0:
                        await raisen.click()
                        await self._human_delay(1.0, 1.5)
                        logger.info("  ✅ Selected 'Raisen' district")
                        await page.wait_for_load_state("networkidle")
                    
                except Exception as e:
                    logger.error(f"  ❌ District selection failed: {e}")
                
                # Screenshot after district selection
                await page.screenshot(path="logs/sniper_district_selected.png")
                
                # STEP 4: Market Selection
                logger.info("\n🎯 Market Selection")
                
                try:
                    # Click market dropdown
                    market_dropdown = page.locator("text=Market").first
                    if await market_dropdown.count() > 0:
                        await market_dropdown.click()
                        await self._human_delay(0.5, 1.0)
                    
                    # Uncheck "Select All" and select "All Markets"
                    select_all_market = page.locator("text=Select All").nth(2)
                    if await select_all_market.count() > 0:
                        await select_all_market.click()
                        await self._human_delay(0.3, 0.6)
                    
                    all_markets = page.locator("text=All Markets").first
                    if await all_markets.count() > 0:
                        await all_markets.click()
                        await self._human_delay(1.0, 1.5)
                        logger.info("  ✅ Selected 'All Markets'")
                    
                except Exception as e:
                    logger.warning(f"  ⚠️  Market selection: {e}")
                
                # STEP 5: Submit
                logger.info("\n🚀 Clicking Submit/Go button...")
                
                try:
                    submit_button = page.locator("input[value='Go'], button:has-text('Go'), input[type='submit']").first
                    
                    if await submit_button.count() > 0:
                        await submit_button.click()
                        logger.info("  ✅ Clicked Submit")
                        
                        # Wait for API responses
                        await asyncio.sleep(5)
                        await page.wait_for_load_state("networkidle")
                        
                        logger.info(f"\n🎯 CAPTURED {len(self.captured_data)} API responses")
                        
                        # Parse captured data
                        all_prices = self._parse_json_responses(self.captured_data)
                        
                    else:
                        logger.error("  ❌ Could not find submit button")
                    
                except Exception as e:
                    logger.error(f"  ❌ Submit failed: {e}")
                
                # Final screenshot
                await page.screenshot(path="logs/sniper_results.png")
                
                # Keep browser open for inspection
                await asyncio.sleep(5)
                
                await browser.close()
                
                logger.info(f"\n{'='*70}")
                logger.info(f"✅ SNIPER COMPLETE")
                logger.info(f"Extracted {len(all_prices)} price records")
                logger.info(f"{'='*70}")
                
                return all_prices
                
        except Exception as e:
            logger.error(f"❌ Sniper failed: {e}", exc_info=True)
            return []
    
    def _parse_json_responses(self, responses: List[Dict]) -> List[Dict]:
        """
        Parse captured JSON responses - PRODUCTION VERSION
        Based on actual API structure discovered
        """
        prices = []
        
        logger.info(f"\n📦 Parsing {len(responses)} API responses")
        
        for idx, data in enumerate(responses, 1):
            try:
                # Save for debugging
                with open(f"logs/api_response_{idx}.json", "w") as f:
                    import json
                    json.dump(data, f, indent=2)
                
                # Skip if status false or no data
                if not data.get("status"):
                    logger.info(f"  Response {idx}: status=false, skipping")
                    continue
                
                # Extract records from API structure
                records = None
                
                if "data" in data and isinstance(data["data"], dict):
                    records = data["data"].get("records", [])
                
                if not records or not isinstance(records, list):
                    logger.info(f"  Response {idx}: no records found")
                    continue
                
                logger.info(f"  ✅ Response {idx}: {len(records)} records")
                
                # Parse each record
                for record in records:
                    try:
                        # Extract fields based on ACTUAL API structure
                        commodity = record.get("cmdt_name", "")
                        price_str = record.get("as_on_price", "0")
                        trend = record.get("trend", "stable")  # up/down/stable
                        arrival_str = record.get("as_on_arrival", "0")
                        msp_price_str = record.get("msp_price", "0")
                        date_str = record.get("reported_date", "")  # DD-MM-YYYY
                        cmdt_group = record.get("cmdt_grp_name", "")
                        
                        # Parse price
                        try:
                            modal_price = float(str(price_str).replace(",", "").strip())
                        except:
                            continue
                        
                        # Parse arrival
                        try:
                            arrival = float(str(arrival_str).replace(",", "").strip())
                        except:
                            arrival = None
                        
                        # Parse date (DD-MM-YYYY -> YYYY-MM-DD)
                        try:
                            date_parts = date_str.split("-")
                            if len(date_parts) == 3:
                                source_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                            else:
                                source_date = datetime.now().strftime("%Y-%m-%d")
                        except:
                            source_date = datetime.now().strftime("%Y-%m-%d")
                        
                        if modal_price > 0 and commodity:
                            price_entry = {
                                "crop": commodity.strip(),
                                "mandi": "Madhya Pradesh",  # State-wide average
                                "price_modal": modal_price,
                                "price_min": None,
                                "price_max": None,
                                "price_trend": trend,  # BONUS from API!
                                "source_date": source_date,
                                "state": "Madhya Pradesh",
                                "district": "All",
                                "variety": cmdt_group,
                                "traded_quantity": None,
                                "arrivals_quantity": arrival
                            }
                            prices.append(price_entry)
                    
                    except Exception as e:
                        continue
                
            except Exception as e:
                logger.warning(f"  ⚠️  Response {idx} parse error: {e}")
                continue
        
        logger.info(f"\n✅ EXTRACTED {len(prices)} PRICES")
        
        # Log sample results
        if prices:
            logger.info("\n📊 Sample results:")
            for p in prices[:5]:
                trend_emoji = {"up": "📈", "down": "📉", "stable": "➡️"}.get(p["price_trend"], "➡️")
                logger.info(f"  {trend_emoji} {p['crop']}: ₹{p['price_modal']} ({p['price_trend']})")
        
        return prices
    
    async def _human_delay(self, min_sec: float = 0.5, max_sec: float = 1.5):
        """Random delay to mimic human"""
        await asyncio.sleep(random.uniform(min_sec, max_sec))


# Global instance
sniper = AgmarknetSniper()


# Test
if __name__ == "__main__":
    async def test():
        prices = await sniper.snipe_madhya_pradesh(headless=False)
        
        print(f"\n✅ Sniped {len(prices)} prices")
        print("\nFirst 10:")
        for p in prices[:10]:
            trend_emoji = {"up": "📈", "down": "📉", "stable": "➡️"}.get(p.get('price_trend', 'stable'), "➡️")
            print(f"  {trend_emoji} {p['crop']}: ₹{p['price_modal']} ({p.get('price_trend', 'stable')})")
    
    asyncio.run(test())
