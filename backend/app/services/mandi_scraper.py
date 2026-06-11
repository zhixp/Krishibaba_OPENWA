"""
UPDATED Mandi Price Scraper Service - CORRECT STRUCTURE
Scrapes from /mandi/{state}/{mandi}/{crop} URLs
Based on actual agriplus.in table structure
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from datetime import datetime
import re

from app.services.crop_database import normalize_crop_name, normalize_state_name

logger = logging.getLogger(__name__)


class MandiScraperV2:
    """
    Updated scraper for agriplus.in mandi-specific pages
    URL pattern: /mandi/{state}/{mandi-name}/{crop}
    """
    
    def __init__(self):
        self.base_url = "https://agriplus.in/mandi"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://agriplus.in/'
        }
    
    def slugify_mandi(self, mandi_name: str) -> str:
        """Convert mandi name to URL slug"""
        slug = mandi_name.lower()
        slug = slug.replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        return slug
    
    async def scrape_mandi_crop(
        self,
        crop_name: str,
        mandi_name: str,
        state_name: str = "madhya pradesh"
    ) -> List[Dict]:
        """
        Scrape prices for a specific crop at a specific mandi
        
        Args:
            crop_name: Crop name (e.g., "Wheat", "Soybean")
            mandi_name: Mandi name (e.g., "Krishi upaj mandi samiti-udaipura")
            state_name: State name (default: Madhya Pradesh)
        
        Returns:
            List of price dictionaries with date information
        """
        # Normalize names
        crop_slug = normalize_crop_name(crop_name)
        state_slug = normalize_state_name(state_name)
        mandi_slug = self.slugify_mandi(mandi_name)
        
        if not crop_slug or not state_slug:
            logger.error(f"Invalid crop or state: {crop_name}, {state_name}")
            return []
        
        url = f"{self.base_url}/{state_slug}/{mandi_slug}/{crop_slug}"
        logger.info(f"Scraping: {url}")
        
        prices = []
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table with id="market-specific-table"
            table = soup.find('table', id='market-specific-table')
            
            if not table:
                # Try finding by class
                table = soup.find('table', class_='price-table')
            
            if not table:
                logger.warning(f"No price table found at {url}")
                return []
            
            tbody = table.find('tbody')
            if not tbody:
                logger.warning("No tbody found in table")
                return []
            
            rows = tbody.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                
                # Table has 6 columns:
                # [0: Price Date, 1: Commodity Traded, 2: Commodity Arrivals,
                #  3: Min Price, 4: Max Price, 5: Modal Price]
                if len(cols) < 6:
                    continue
                
                price_date = cols[0].text.strip()
                traded_qty = cols[1].text.strip()
                arrivals_qty = cols[2].text.strip()
                min_price = cols[3].text.strip()
                max_price = cols[4].text.strip()
                modal_price = cols[5].text.strip()
                
                # Parse prices
                try:
                    modal_price_clean = float(modal_price.replace(',', '').strip()) if modal_price else None
                    min_price_clean = float(min_price.replace(',', '').strip()) if min_price else None
                    max_price_clean = float(max_price.replace(',', '').strip()) if max_price else None
                except ValueError:
                    logger.warning(f"Invalid price format: {modal_price}")
                    continue
                
                if not modal_price_clean:
                    continue
                
                # Parse date (format: "14 Nov" or "15 Sep")
                # We need to add the year
                current_year = datetime.now().year
                try:
                    # Try parsing with current year
                    date_with_year = f"{price_date} {current_year}"
                    date_obj = datetime.strptime(date_with_year, "%d %b %Y")
                    
                    # If parsed date is in future, use previous year
                    if date_obj > datetime.now():
                        date_obj = datetime.strptime(f"{price_date} {current_year - 1}", "%d %b %Y")
                    
                    date_scraped = date_obj.strftime("%Y-%m-%d")
                    date_display = price_date  # Keep original format for display
                except ValueError:
                    logger.warning(f"Could not parse date: {price_date}")
                    date_scraped = datetime.now().strftime("%Y-%m-%d")
                    date_display = price_date
                
                price_entry = {
                    'crop_name': crop_name,
                    'mandi_location': mandi_name,
                    'variety': 'General',  # This table doesn't have variety column
                    'modal_price': modal_price_clean,
                    'min_price': min_price_clean,
                    'max_price': max_price_clean,
                    'date_scraped': date_scraped,
                    'date_display': date_display,  # Human-readable date
                    'traded_quantity': traded_qty,
                    'arrivals_quantity': arrivals_qty,
                    'state': state_name.title(),
                    'district': None,  # Extract from mandi name if possible
                    'data_freshness': self._calculate_freshness(date_scraped)
                }
                
                prices.append(price_entry)
            
            logger.info(f"Scraped {len(prices)} price entries from {mandi_name}")
            return prices
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error on {url}: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Scraping error on {url}: {e}")
            return []
    
    def _calculate_freshness(self, date_str: str) -> str:
        """
        Calculate how fresh the data is
        
        Returns: "today", "this_week", "this_month", "old"
        """
        try:
            price_date = datetime.strptime(date_str, "%Y-%m-%d")
            today = datetime.now()
            days_old = (today - price_date).days
            
            if days_old == 0:
                return "today"
            elif days_old <= 7:
                return "this_week"
            elif days_old <= 30:
                return "this_month"
            else:
                return "old"
        except:
            return "unknown"
    
    async def scrape_popular_mandis(
        self,
        crop_name: str,
        state_name: str = "madhya pradesh"
    ) -> List[Dict]:
        """
        Scrape multiple popular mandis for a crop
        
        Args:
            crop_name: Crop name
            state_name: State name
        
        Returns:
            Combined list of prices from popular mandis
        """
        # Popular mandis in Madhya Pradesh
        popular_mandis = [
            "krishi-upaj-mandi-samiti-bhopal",
            "krishi-upaj-mandi-samiti-indore",
            "krishi-upaj-mandi-samiti-udaipura",
            "krishi-upaj-mandi-samiti-vidisha",
            "krishi-upaj-mandi-samiti-raisen"
        ]
        
        all_prices = []
        
        for mandi in popular_mandis:
            prices = await self.scrape_mandi_crop(
                crop_name=crop_name,
                mandi_name=mandi,
                state_name=state_name
            )
            all_prices.extend(prices)
        
        return all_prices


# Global scraper instance
mandi_scraper_v2 = MandiScraperV2()
