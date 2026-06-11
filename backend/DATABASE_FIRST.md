# 🚜 Krishi Baba - Database-First Architecture

## Philosophy

**"Serve Stale Data > Serve No Data"**

- ✅ **NEVER** scrape on user request
- ✅ **ALWAYS** serve from database
- ✅ **Warn** users if data is stale
- ✅ **Track** price movements over time

---

## Architecture Overview

```
User Request → API → Database (price_history) → Response
                         ↑
            Background Scraper (Cron)
                         ↑
                    Agmarknet.gov.in
```

---

## Database Schema

### mandi_price_history Table

**Purpose:** Store ALL historical prices for movement tracking

| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER | PK, auto-increment |
| crop | TEXT | Indexed (e.g., "Soybean") |
| mandi | TEXT | Indexed (e.g., "Raisen") |
| price_min | REAL | Minimum price |
| price_max | REAL | Maximum price |
| price_modal | REAL | Modal (most common) price |
| scraped_at | TIMESTAMP | When we scraped it |
| source_date | DATE | When mandi reported it |
| state | TEXT | State name |
| district | TEXT | District name |
| traded_quantity | TEXT | Amount traded |
| arrivals_quantity | TEXT | Amount arrived |

**Indexes:**
- `(crop)` - Fast crop lookups
- `(mandi)` - Fast mandi lookups
- `(source_date DESC)` - Latest first
- `(crop, mandi, source_date DESC)` - Combined lookup

**Unique Constraint:** `(crop, mandi, source_date)` - No duplicates per day

---

## API Logic (/chat/interact)

### Query Flow

```python
# User asks: "Bhopal mein soybean ka bhav?"

# 1. Query latest price
price_data = await price_query_service.get_latest_price(
    db=db,
    crop="Soybean",
    location="Bhopal"
)

# 2. Check staleness
if price_data:
    if price_data['is_stale']:
        # Serve with orange warning 🟠
        status = "kal ka bhav (yesterday's price)"
    else:
        # Serve fresh data 🟢
        status = "taaza bhav (fresh price)"

# 3. Get price movement (if available)
movement = await price_query_service.get_price_movement(
    db=db,
    crop="Soybean",
    mandi="Bhopal"
)

# Returns: "📈 पिछली बार से ₹50 बढ़ा"
```

### Staleness Levels

| Days Old | Status | Badge | Hindi |
|----------|--------|-------|-------|
| 0 | fresh | 🟢 | ताज़ा भाव |
| 1 | yesterday | 🟡 | कल का भाव |
| 2-7 | this_week | 🟠 | X दिन पुराना |
| 8+ | stale | 🔴 | पुराना डेटा |

---

## Background Scraper (Watchdog)

### Run Schedule

**Cron:** Daily at 4:00 AM IST

```bash
0 4 * * * cd /path/to/backend && python scripts/watchdog.py
```

### Watchdog Logic

```python
try:
    # Run scraper
    result = await run_scraper()
    
    if result == 0:
        # WARNING: Site might be down
        send_alert("⚠️  0 records scraped")
    else:
        # SUCCESS
        print(f"✅ {result} records inserted")
        
except Exception as e:
    # CRITICAL ERROR
    send_alert(f"🔥 Scraper crashed: {e}")
    
    # DON'T crash system
    # App continues with stale data
```

### What It Does

1. **Scrapes** mandi prices from agmarknet.gov.in
2. **Appends** new data to `mandi_price_history` (doesn't overwrite)
3. **Logs** success/failure
4. **Alerts** admin if scraper fails (Telegram/Email)
5. **Exits gracefully** - system continues even if scraper fails

---

## Response Examples

### Fresh Data (< 24 hours old)

**User:** "Bhopal mein soybean ka bhav?"

**API Response:**
```json
{
  "reply_text_hindi": "भाई, **12 Dec** को Bhopal में सोयाबीन का भाव **₹4300 प्रति क्विंटल** है 🟢\n📈 पिछली बार से ₹50 बढ़ा। अच्छा समय है बेचने का!",
  "card_data": {
    "price_modal": 4300,
    "date": "12 Dec",
    "is_stale": false,
    "freshness": "fresh",
    "price_movement": "📈 पिछली बार से ₹50 बढ़ा"
  }
}
```

### Stale Data (> 7 days old)

**User:** "Udaipura mein gehun ka bhav?"

**API Response:**
```json
{
  "reply_text_hindi": "भाई, **14 Nov** को Udaipura में गेहूं का भाव था **₹2550 प्रति क्विंटल** 🟠\nयह पुराना डेटा है (28 दिन पुराना)। ताज़ा भाव के लिए मंडी से संपर्क करें।",
  "card_data": {
    "price_modal": 2550,
    "date": "14 Nov",
    "is_stale": true,
    "freshness": "stale",
    "days_old": 28
  }
}
```

---

## UI Integration

Phase 1 UI is WhatsApp text output. Keep mandi responses as structured backend payloads so future clients can render freshness, movement, and nearby market data without changing the mandi engine.


## Alert System (Future)

### Telegram Bot Integration

```python
async def send_telegram_alert(message: str):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    await httpx.post(url, json={
        "chat_id": chat_id,
        "text": f"🚨 Krishi Baba Alert:\n\n{message}",
        "parse_mode": "Markdown"
    })
```

---

## Testing

### Test Staleness Detection

```bash
cd backend
python -c "
from app.services.price_query import price_query_service
import asyncio
from app.database.db import get_db

async def test():
    async for db in get_db():
        price = await price_query_service.get_latest_price(
            db=db,
            crop='Wheat',
            location='Bhopal'
        )
        print(f'Price: ₹{price[\"price_modal\"]}')
        print(f'Is Stale: {price[\"is_stale\"]}')
        print(f'Days Old: {price[\"days_old\"]}')

asyncio.run(test())
"
```

### Run Watchdog Manually

```bash
cd backend
python scripts/watchdog.py
```

---

## Next Steps

### Phase 3B: Agmarknet Scraper

**Tools:** Playwright (headless browser)

**Why:** Agmarknet uses ASP.NET forms with `__VIEWSTATE` - can't use simple requests

**Implementation:**
```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    
    # Navigate to search page
    await page.goto("https://agmarknet.gov.in/SearchCmmMkt.aspx")
    
    # Select state, commodity, etc.
    await page.select_option("#ddlState", "MP")
    await page.select_option("#ddlCommodity", "Soybean")
    await page.click("#btnSearch")
    
    # Parse table
    table = await page.query_selector("table.price-table")
    # Extract data...
```

**Complexity:** Medium (1-2 hours)

**When:** After the WhatsApp channel endpoint and mandi warehouse are stable

---

## Summary

✅ **Database-first** - Never scrape on user request  
✅ **Stale data handling** - Orange warning if old  
✅ **Price movement** - Show trends (up/down/stable)  
✅ **Watchdog system** - Graceful failure handling  
✅ **Alert ready** - Telegram integration placeholder  

**Philosophy:** Better to show yesterday's price than no price! 🚜
