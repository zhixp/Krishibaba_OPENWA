"""
🚜 MANDI PRICE SCRAPER - The Night Owl
Runs independently, scrapes Agmarknet, saves to DB
Chatbot only READS the cache (never scrapes live)
"""
import sqlite3
import requests
import datetime
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CONFIG
DB_PATH = "krishi_baba.db"
TARGET_COMMODITIES = {
    "Soyabean": "23",
    "Wheat": "14",
    "Rice": "17",
    "Cotton": "60"
}

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create mandi_prices table if not exists"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mandi_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commodity TEXT NOT NULL,
            market TEXT NOT NULL,
            min_price REAL,
            max_price REAL,
            modal_price REAL,
            date TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("✅ DB initialized with mandi_prices table")

def scrape_agmarknet(commodity_name: str, commodity_code: str):
    """
    Scrape Agmarknet for a specific commodity
    Returns list of (commodity, market, min, max, modal, date) tuples
    """
    today = datetime.datetime.now().strftime("%d-%b-%Y")
    
    # Agmarknet URL (Madhya Pradesh, All Districts, All Markets)
    url = f"https://agmarknet.gov.in/SearchCmmMkt.aspx?Tx_Commodity={commodity_code}&Tx_State=MP&Tx_District=0&Tx_Market=0&DateFrom={today}&DateTo={today}&Fr_Date={today}&To_Date={today}&Tx_Trend=0&Tx_CommodityHead={commodity_name}&Tx_StateHead=Madhya+Pradesh&Tx_DistrictHead=--Select--&Tx_MarketHead=--Select--"
    
    try:
        logger.info(f"🔍 Fetching {commodity_name} prices from Agmarknet...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP {response.status_code} for {commodity_name}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'cphBody_GridPriceData'})
        
        if not table:
            logger.warning(f"⚠️ No price table found for {commodity_name}")
            return []
        
        rows = table.find_all('tr')[1:]  # Skip header
        data = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 8:
                try:
                    market = cols[1].text.strip()
                    min_price = float(cols[5].text.strip()) if cols[5].text.strip() else 0
                    max_price = float(cols[6].text.strip()) if cols[6].text.strip() else 0
                    modal_price = float(cols[7].text.strip()) if cols[7].text.strip() else 0
                    date_str = cols[9].text.strip() if len(cols) > 9 else today
                    
                    data.append((commodity_name, market, min_price, max_price, modal_price, date_str))
                except (ValueError, IndexError) as e:
                    logger.warning(f"Skipping malformed row: {e}")
                    continue
        
        logger.info(f"✅ Scraped {len(data)} records for {commodity_name}")
        return data
    
    except Exception as e:
        logger.error(f"❌ Scraping failed for {commodity_name}: {e}")
        return []

def update_cache():
    """
    Main function: Scrape all commodities and update DB
    """
    logger.info("=" * 70)
    logger.info("🚜 MANDI SCRAPER STARTED")
    logger.info("=" * 70)
    
    init_db()
    
    all_data = []
    
    # Scrape each commodity
    for commodity_name, commodity_code in TARGET_COMMODITIES.items():
        data = scrape_agmarknet(commodity_name, commodity_code)
        all_data.extend(data)
    
    if not all_data:
        logger.warning("⚠️ No data scraped. Is Agmarknet down?")
        return
    
    # Update database (replace old data with fresh)
    conn = get_db_connection()
    
    # Clear old data (keep it simple - latest snapshot only)
    conn.execute("DELETE FROM mandi_prices")
    
    # Insert new data
    conn.executemany("""
        INSERT INTO mandi_prices (commodity, market, min_price, max_price, modal_price, date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, all_data)
    
    conn.commit()
    
    # Verify
    count = conn.execute("SELECT COUNT(*) FROM mandi_prices").fetchone()[0]
    conn.close()
    
    logger.info("=" * 70)
    logger.info(f"✅ CACHE UPDATED: {count} price records saved to DB")
    logger.info(f"📅 Data Date: {datetime.datetime.now().strftime('%d-%b-%Y')}")
    logger.info("=" * 70)

if __name__ == "__main__":
    update_cache()
