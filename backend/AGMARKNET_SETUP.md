# Agmarknet Official Scraper Setup

## Install Playwright

```bash
cd backend
pip install playwright
playwright install chromium
```

This downloads ~300MB Chromium browser (one-time)

## Test Scraper

```bash
python test_agmarknet.py
```

**Expected:** Scrapes real government data from agmarknet.gov.in!

## Why Playwright?

Agmarknet uses ASP.NET forms with:
- `__VIEWSTATE` tokens (anti-scraping)
- Dynamic dropdowns
- JavaScript validation

Simple `requests` won't work. Playwright acts like a real browser.

## Production Cron

```bash
# Daily at 4 AM
0 4 * * * cd /path/to/backend && python scripts/watchdog.py
```

Watchdog will use agmarknet_scraper automatically!

## Data Source

✅ **Official:** agmarknet.gov.in (Government of India)  
✅ **Accurate:** Direct from mandi records  
✅ **Complete:** All states, all commodities  

**No more third-party aggregators!** 🎉
