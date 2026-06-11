"""
AGMARKNET API SCRAPER - Direct API Mode
Discovered API endpoint: /api/v1/dashboard-filters/?dashboard_name=marketwise_price_arrival
No complex UI clicking needed - just call the API directly!
"""
import httpx
from typing import List, Dict
from datetime import datetime
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgmarknetAPI:
    """
    Direct API scraper - bypasses UI completely!
    Discovered from network intercept: marketwise_price_arrival API
    """
    
    def __init__(self):
        self.base_url = "https://agmarknet.gov.in"
        self.api_path = "/api/v1/dashboard-filters/"
        
        # State codes (discovered from API)
        self.states = {
            "Madhya Pradesh": 19,
            "Uttar Pradesh": 36,
            "Rajasthan": 27
        }
    
    async def fetch_state_prices(
        self,
        state_name: str = "Madhya Pradesh",
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch prices directly via API
        
        Args:
            state_name: State to fetch
            limit: Max records to fetch
        
        Returns:
            List of price dictionaries
        """
        logger.info(f"🎯 DIRECT API MODE: {state_name}")
        
        state_code = self.states.get(state_name)
        if not state_code:
            logger.error(f"Unknown state: {state_name}")
            return []
        
        # Construct API URL
        url = f"{self.base_url}{self.api_path}"
        params = {
            "dashboard_name": "marketwise_price_arrival",
            "state": f"[{state_code}]",
            "limit": limit
        }
        
        logger.info(f"📡 Calling API: {url}")
        logger.info(f"📊 Params: {params}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"✅ API Response received")
                logger.info(f"📦 Keys: {list(data.keys())}")
                
                # Parse response
                prices = self._parse_api_response(data, state_name)
                
                logger.info(f"✅ Extracted {len(prices)} prices from API")
                return prices
                
        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            return []
    
    def _parse_api_response(self, data: Dict, state: str) -> List[Dict]:
        """Parse API JSON response"""
        prices = []
        
        try:
            # Try different possible structures
            records = None
            
            if "data" in data:
                if isinstance(data["data"], list):
                    records = data["data"]
                elif isinstance(data["data"], dict) and "records" in data["data"]:
                    records = data["data"]["records"]
            elif "records" in data:
                records = data["records"]
            
            if not records:
                logger.warning("No records found in API response")
                logger.info(f"Response structure: {data}")
                return []
            
            logger.info(f"Found {len(records)} records")
            
            for record in records:
                try:
                    # Extract fields (adjust based on actual API structure)
                    commodity = record.get("commodity", record.get("cmdt_name", ""))
                    price_str = record.get("modal_price", record.get("as_on_price", record.get("price", "0")))
                    trend = record.get("trend", "stable")
                    market = record.get("market", record.get("market_name", state))
                    district = record.get("district", "All")
                    arrival = record.get("arrival", None)
                    
                    # Parse price
                    try:
                        modal_price = float(str(price_str).replace(",", ""))
                    except:
                        continue
                    
                    if modal_price > 0:
                        price_entry = {
                            "crop": commodity.strip(),
                            "mandi": market,
                            "price_modal": modal_price,
                            "price_min": None,
                            "price_max": None,
                            "price_trend": trend,  # BONUS!
                            "source_date": datetime.now().strftime("%Y-%m-%d"),
                            "state": state,
                            "district": district,
                            "variety": "General",
                            "traded_quantity": None,
                            "arrivals_quantity": arrival
                        }
                        prices.append(price_entry)
                
                except Exception as e:
                    continue
            
            return prices
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return []
    
    async def scrape_all_states(self) -> List[Dict]:
        """Scrape all configured states"""
        all_prices = []
        
        for state_name in self.states.keys():
            logger.info(f"\n{'='*70}")
            logger.info(f"STATE: {state_name}")
            logger.info(f"{'='*70}")
            
            prices = await self.fetch_state_prices(state_name)
            all_prices.extend(prices)
            
            await asyncio.sleep(1)  # Small delay between states
        
        return all_prices


# Global instance
agmarknet_api = AgmarknetAPI()


# Test
if __name__ == "__main__":
    async def test():
        print("="*70)
        print("🎯 AGMARKNET DIRECT API SCRAPER")
        print("="*70)
        
        # Test single state
        prices = await agmarknet_api.fetch_state_prices("Madhya Pradesh")
        
        print(f"\n✅ Got {len(prices)} prices")
        print("\nFirst 10:")
        for p in prices[:10]:
            trend_emoji = {"up": "📈", "down": "📉", "stable": "➡️"}.get(p.get('price_trend', 'stable'), "➡️")
            print(f"  {trend_emoji} {p['crop']}: ₹{p['price_modal']} ({p.get('price_trend', 'stable')})")
    
    asyncio.run(test())
