# Daily Price Update Setup

## 🕐 Scheduling Strategy

**Goal:** Update prices once daily to build accurate historical data

**Best Time:** 4:00 AM IST (after mandis close and upload data)

**What Happens:**
1. Scraper runs via watchdog
2. Fetches last 30 days of data from agmarknet
3. **APPENDS** new prices to `mandi_price_history` (doesn't delete old)
4. Over time, you build months/years of price history
5. App shows price movements: "📈 ₹50 बढ़ा"

---

## Windows Task Scheduler Setup

### Step 1: Create Batch File

Create `run_scraper.bat` in `backend/` folder:

```batch
@echo off
cd /d "D:\BUILDS_TOOLS\Krishi baba App\backend"
python scripts\watchdog.py >> logs\scraper.log 2>&1
```

### Step 2: Open Task Scheduler

1. Press `Win + R` → type `taskschd.msc` → Enter
2. Click "Create Basic Task"

### Step 3: Configure Task

**General Tab:**
- Name: `Krishi Baba Daily Price Update`
- Description: `Scrapes mandi prices from agmarknet.gov.in`
- ✅ Run whether user is logged on or not
- ✅ Run with highest privileges

**Triggers Tab:**
- New → Daily
- Start: `4:00:00 AM`
- Recur every: `1 days`

**Actions Tab:**
- Action: `Start a program`
- Program/script: `D:\BUILDS_TOOLS\Krishi baba App\backend\run_scraper.bat`
- Start in: `D:\BUILDS_TOOLS\Krishi baba App\backend`

**Conditions Tab:**
- ✅ Start only if computer is on AC power (for laptops)
- ✅ Wake the computer to run this task

**Settings Tab:**
- ✅ Allow task to be run on demand
- If task fails, restart every: `10 minutes`
- Attempt to restart: `3 times`

### Step 4: Test

Right-click task → "Run"

Check `backend/logs/scraper.log` for output

---

## Linux/Mac Cron Setup

### Step 1: Create Cron Job

```bash
crontab -e
```

### Step 2: Add Line

```bash
# Run daily at 4 AM IST
0 4 * * * cd /path/to/backend && /usr/bin/python3 scripts/watchdog.py >> logs/scraper.log 2>&1
```

### Step 3: Check Timezone

```bash
timedatectl  # Should show IST
```

If not IST, adjust cron time accordingly.

### Step 4: Verify Cron

```bash
crontab -l   # List cron jobs
```

---

## Manual Run (For Testing)

```bash
cd backend
python scripts/watchdog.py
```

**Output:**
```
🌾 Starting OFFICIAL Agmarknet scraper...
Source: agmarknet.gov.in (Government of India)

📍 Scraping Madhya Pradesh...
  ✅ Inserted 156 entries from Madhya Pradesh

📍 Scraping Uttar Pradesh...
  ✅ Inserted 203 entries from Uttar Pradesh

✅ Scraper completed: 359 new entries
```

---

## How Historical Data Builds

### Database Strategy

**Table:** `mandi_price_history`  
**Unique Constraint:** `(crop, mandi, source_date)`

**What This Means:**
- Same price on same date = ignored (no duplicates)
- Different dates = appended to history
- Over 30 days = 30 historical prices per mandi per crop
- Over 1 year = 365 price points!

### Example Timeline

**Day 1 (Dec 12):**
```sql
SELECT * FROM mandi_price_history WHERE crop='Wheat' AND mandi='Bhopal'
-- Results: 1 row (Dec 12)
```

**Day 2 (Dec 13):**
```sql
-- After scraper runs
-- Results: 2 rows (Dec 12, Dec 13)
```

**Day 30:**
```sql
-- Results: 30 rows (full month of prices)
```

**Now you can show:**
- "Price increased ₹50 since yesterday"
- "This week average: ₹4250"
- "30-day trend: 📈 Upward"

---

## Logs & Monitoring

### Create Logs Directory

```bash
cd backend
mkdir logs
```

### View Logs

**Windows:**
```powershell
Get-Content logs\scraper.log -Tail 50
```

**Linux/Mac:**
```bash
tail -f logs/scraper.log
```

### Log Rotation (Linux)

Create `/etc/logrotate.d/krishi-baba`:

```
/path/to/backend/logs/scraper.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

---

## Alert on Failure (Optional)

### Email Alerts

Update `scripts/watchdog.py` - add to `.env`:

```bash
ALERT_EMAIL=your@email.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=bot@gmail.com
SMTP_PASSWORD=app_password
```

### Telegram Bot (Recommended)

1. Create bot: Talk to @BotFather on Telegram
2. Get token and chat ID
3. Add to `.env`:

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_ADMIN_CHAT_ID=987654321
```

Watchdog already has placeholder for this!

---

## Monitoring Dashboard (Future)

### Quick Status Check

```bash
cd backend
python -c "
from app.database.db import get_db
import asyncio
import sqlite3

async def check():
    async for db in get_db():
        # Latest scrape
        cursor = await db.execute(
            'SELECT MAX(scraped_at) as last_scrape FROM mandi_price_history'
        )
        row = await cursor.fetchone()
        print(f'Last scrape: {row[0]}')
        
        # Total records
        cursor = await db.execute('SELECT COUNT(*) FROM mandi_price_history')
        count = await cursor.fetchone()
        print(f'Total records: {count[0]:,}')
        
        # Unique crops
        cursor = await db.execute('SELECT COUNT(DISTINCT crop) FROM mandi_price_history')
        crops = await cursor.fetchone()
        print(f'Crops tracked: {crops[0]}')

asyncio.run(check())
"
```

**Output:**
```
Last scrape: 2025-12-12 04:00:15
Total records: 12,456
Crops tracked: 8
```

---

## Expected Data Growth

| Timeframe | Records per State | Total (3 states) |
|-----------|-------------------|------------------|
| Day 1 | ~150 | ~450 |
| Week 1 | ~1,000 | ~3,000 |
| Month 1 | ~4,500 | ~13,500 |
| Year 1 | ~55,000 | ~165,000 |

**Database Size:** ~50MB after 1 year (SQLite is efficient!)

---

## Production Checklist

- [ ] Install Playwright: `pip install playwright`
- [ ] Install browser: `playwright install chromium`
- [ ] Create logs directory: `mkdir backend/logs`
- [ ] Set up scheduled task (Windows) OR cron (Linux)
- [ ] Test manual run: `python scripts/watchdog.py`
- [ ] Verify data: Check `mandi_price_history` table
- [ ] Monitor first week (check logs daily)
- [ ] Set up alerts (optional but recommended)

---

## Troubleshooting

### "Playwright not found"
```bash
pip install playwright
playwright install chromium
```

### "No data scraped"
- Check agmarknet.gov.in is accessible
- Verify Playwright browser installed
- Check logs for specific errors

### "Duplicate data warnings"
Normal! `INSERT OR IGNORE` prevents duplicates.

### "Disk space full"
Historical data grows. Clean old data:
```sql
DELETE FROM mandi_price_history 
WHERE source_date < date('now', '-1 year');
```

---

## 🎉 You're Set!

Once scheduled:
- ✅ Prices update daily at 4 AM
- ✅ Historical data builds automatically
- ✅ Users see accurate, fresh data
- ✅ Price movements tracked
- ✅ 100% offline-first (after first sync)

**Your farmers will have the most accurate mandi prices in India!** 🚜
