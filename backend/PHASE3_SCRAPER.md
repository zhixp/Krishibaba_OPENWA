# Phase 3: Data Services - Mandi Scraper

## ✅ What We Built

### 1. Mandi Price Scraper

**Source:** agriplus.in (same as your working WhatsApp version!)

#### Files Created:
- [crop_database.py](file:///d:/BUILDS_TOOLS/Krishi%20baba%20App/backend/app/services/crop_database.py) - Maps Hindi/English crop names to URLs
- [mandi_scraper.py](file:///d:/BUILDS_TOOLS/Krishi%20baba%20App/backend/app/services/mandi_scraper.py) - Async scraper with BeautifulSoup
- [test_scraper.py](file:///d:/BUILDS_TOOLS/Krishi%20baba%20App/backend/test_scraper.py) - Test suite
- [daily_update.py](file:///d:/BUILDS_TOOLS/Krishi%20baba%20App/backend/scripts/daily_update.py) - Cron job script

---

## 🧪 Testing the Scraper

### Quick Test

```bash
cd backend
python test_scraper.py
```

**What it tests:**
- ✅ Single crop scraping (Wheat from MP)
- ✅ Hindi crop names (धान works!)
- ✅ Mandi filtering (get specific mandi prices)
- ✅ Multiple crops at once
- ✅ Database of 70+ crops and 10+ states

**Expected output:**
```
✅ Found 5 price entries:
  1. Bhopal (Bhopal)
     Variety: Desi
     Price: ₹4200/quintal
     Range: ₹3900 - ₹4500
     Date: 2025-12-12
```

---

## 🌾 Supported Crops

**80+ crops** including:
- Grains: Wheat, Paddy, Maize, Bajra, Jowar
- Pulses: Soybean, Gram, Arhar, Moong, Urad, Masur
- Oil: Groundnut, Mustard, Sesame, Sunflower
- Cash: Cotton, Sugarcane
- Spices: Turmeric, Chili, Coriander, Cumin
- Vegetables: Onion, Potato, Tomato

Works with **Hindi or English** names!

---

## 📍 Supported States

- Madhya Pradesh
- Uttar Pradesh
- Rajasthan
- Maharashtra  
- Punjab
- Haryana
- Bihar
- And more...

---

## 🔄 Daily Auto-Update

### Manual Run

```bash
cd backend
python scripts/daily_update.py
```

Updates database with fresh prices for:
- 10 priority crops
- 4 major states  
- ~400 new price entries daily
- Auto-deletes prices older than 30 days

### Set Up Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 4 AM)
0 4 * * * cd /path/to/backend && python scripts/daily_update.py
```

### Set Up Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task > Daily > 4:00 AM
3. Action: Start a program
4. Program: `python`
5. Arguments: `scripts\daily_update.py`
6. Start in: `d:\BUILDS_TOOLS\Krishi baba App\backend`

---

## 💡 Usage in API

Already integrated! The chat endpoint uses scraped data:

**User:** "Bhopal ka gehun ka bhav kya hai?"

**Backend:**
1. AI classifies intent → `mandi`
2. Extracts location → `Bhopal`
3. Queries database (populated by scraper)
4. Returns price + AI explanation

---

## 🐛 Troubleshooting

### "No prices found"
- Check internet connection
- Verify crop name exists: `python -c "from app.services.crop_database import get_available_crops; print(get_available_crops())"`
- Try different state

### "Scraping slow"
- Normal! Each page takes 1-2 seconds
- Reduce `max_results` parameter

### "Rate limited"
- Add delays: `await asyncio.sleep(2)`
- Use rotating user agents (future enhancement)

---

## 📊 Data Quality

**Pros:**
- ✅ Real-time prices
- ✅ Multiple mandis per crop
- ✅ Variety information
- ✅ Min/Max/Modal prices
- ✅ Proven working (from WhatsApp version)

**Limitations:**
- Data depends on agriplus.in availability
- Not all mandis report daily
- Some crops have limited data

---

## 🎯 Next: Weather Service

Coming next in Phase 3:
- OpenWeather API integration
- Weather-based advice
- Forecast for farmers

**Play Store Account:** Wait until Phase 7 (Play Store Compliance). No rush! 🚀
