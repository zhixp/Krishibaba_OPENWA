"""
Production Chat Endpoint - 3 Specialized Agents
"""
from fastapi import APIRouter, Depends, File, UploadFile, Form
from app.models.schemas import ChatResponse
from app.database.db import get_db
from app.services.weather_agent import weather_agent
from app.services.mandi_agent import mandi_agent
from app.services.sarpanch_agent import sarpanch_agent
from app.services.weather_service import weather_service
from app.services.chat_memory import chat_memory
from app.services.user_profile import user_profile
import aiosqlite
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["Sarpanch AI"])


# ============================================================================
# 1. WEATHER AGENT - Forecast Analysis
# ============================================================================

@router.post("/weather/report")
async def get_weather_report(
    uid: str = Form(...),
    pincode: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Weather Agent: 3-day forecast with farming advice
    """
    try:
        # Get user location
        cursor = await db.execute(
            "SELECT lat, long, default_district FROM users WHERE uid = ?", 
            (uid,)
        )
        user = await cursor.fetchone()
        
        if not user or (not user[0] and not pincode):
            return {
                "success": False,
                "message": "❌ लोकेशन नहीं मिली। कृपया पहले लोकेशन सेट करें।"
            }
        
        lat, lon, district = user[0], user[1], user[2]
        
        # Override with pincode if provided
        if pincode:
            loc_data = await weather_service.geocode_location(pincode)
            if loc_data:
                lat, lon = loc_data['lat'], loc_data['lon']
                district = loc_data.get('district', pincode)
        
        # Fetch weather data
        current = await weather_service.get_current_weather(lat, lon)
        forecast = await weather_service.get_forecast(lat, lon, days=3)
        
        if not current or not forecast:
            return {
                "success": False,
                "message": "❌ मौसम का डेटा नहीं मिल सका। बाद में कोशिश करें।"
            }
        
        # Get user profile for personalized advice
        profile_context = await user_profile.get_formatted_context(db, uid)
        
        # WEATHER AGENT: Analyze forecast
        weather_advice = await weather_agent.analyze_forecast(
            forecast_data=forecast,
            location=district,
            user_profile=profile_context
        )
        
        return {
            "success": True,
            "location": f"📍 {district}",
            "current": {
                "temp": f"{current.get('temp')}°C",
                "condition": current.get('description'),
                "humidity": f"{current.get('humidity')}%",
                "icon": current.get('icon')
            },
            "forecast": [
                {
                    "date": day.get('date'),
                    "temp_min": day.get('temp_min'),
                    "temp_max": day.get('temp_max'),
                    "condition": day.get('description'),
                    "rain_chance": f"{day.get('rain_probability', 0)}%",
                    "icon": day.get('icon')
                }
                for day in forecast[:3]
            ],
            "advice": f"💬  {weather_advice}"
        }
    
    except Exception as e:
        logger.error(f"Weather error: {e}", exc_info=True)
        return {
            "success": False,
            "message": "❌ कुछ गड़बड़ हो गई। बाद में कोशिश करें।"
        }


# ============================================================================
# 2. MANDI AGENT - Price Analysis
# ============================================================================

@router.post("/mandi/prices")
async def get_mandi_prices(
    uid: str = Form(...),
    crop: str = Form(...),
    location: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Mandi Agent: Price data + market insights
    """
    try:
        # Query database
        query = """
            SELECT crop, mandi, price_modal, price_min, price_max, 
                   source_date, state, district
            FROM mandi_price_history
            WHERE crop LIKE ?
        """
        params = [f"%{crop}%"]
        
        if location and location != "सभी मंडियाँ":
            query += " AND (mandi LIKE ? OR district LIKE ?)"
            params.extend([f"%{location}%", f"%{location}%"])
        
        query += " ORDER BY source_date DESC LIMIT 20"
        
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        
        if not rows:
            return {
                "success": False,
                "message": f"❌ {crop} का भाव नहीं मिला। दूसरी फसल चुनें।"
            }
        
        # Build price list
        prices = []
        for row in rows:
            prices.append({
                "crop": row[0],
                "mandi": row[1],
                "price_modal": int(row[2]),
                "modal_price": f"₹{int(row[2])}",
                "min_price": f"₹{int(row[3])}" if row[3] else "N/A",
                "max_price": f"₹{int(row[4])}" if row[4] else "N/A",
                "date": row[5],
                "state": row[6] or "",
                "district": row[7] or ""
            })
        
        # Get user profile
        profile_context = await user_profile.get_formatted_context(db, uid)
        
        # MANDI AGENT: Analyze prices
        market_advice = await mandi_agent.analyze_prices(
            crop=crop,
            prices=prices,
            user_profile=profile_context
        )
        
        # Summary
        highest_price = max(p['price_modal'] for p in prices)
        highest_mandi = next(p['mandi'] for p in prices if p['price_modal'] == highest_price)
        
        return {
            "success": True,
            "crop": f"🌾 {crop.upper()}",
            "location": location or "सभी मंडियाँ",
            "prices": prices,
            "summary": f"सबसे ज्यादा भाव {highest_mandi} में ₹{int(highest_price)}",
            "advice": f"💬 {market_advice}"
        }
    
    except Exception as e:
        logger.error(f"Mandi error: {e}", exc_info=True)
        return {
            "success": False,
            "message": "❌ कुछ गड़बड़ हो गई। बाद में कोशिश करें।"
        }


# ============================================================================
# 3. SARPANCH AGENT - Main Farming Chat
# ============================================================================

@router.post("/chat/advice")
async def ask_kisan_baba(
    uid: str = Form(...),
    message: str = Form(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Sarpanch AI: General farming advice with memory
    """
    try:
        # Get user profile
        profile = await user_profile.get_profile(db, uid)
        profile_context = await user_profile.get_formatted_context(db, uid)
        
        # Get chat history (last 20 messages)
        chat_history = await chat_memory.get_formatted_history(db, uid, limit=20)
        
        # Check if greeting
        if sarpanch_agent.is_greeting(message):
            reply = f"राम राम {profile['name']}! 🙏\n\nक्या समस्या है? पूछो भैया।"
        else:
            # SARPANCH AGENT: Answer farming questions
            reply = await sarpanch_agent.chat(
                message=message,
                user_profile=profile_context,
                chat_history=chat_history
            )
        
        # Save to memory
        await chat_memory.save_message(db, uid, "user", message)
        await chat_memory.save_message(db, uid, "assistant", reply)
        
        return {
            "success": True,
            "reply": reply
        }
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return {
            "success": False,
            "reply": "❌ कुछ गड़बड़ हो गई। बाद में कोशिश करें।"
        }


# ============================================================================
# 4. Image Upload (Beta)
# ============================================================================

@router.post("/disease/detect")
async def upload_disease_image(
    uid: str = Form(...),
    image: UploadFile = File(...),
    crop_type: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Disease image upload for future ML"""
    try:
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = f"{uid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.filename}"
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(await image.read())
        
        await db.execute(
            "INSERT INTO uploaded_images (uid, filename, crop_type) VALUES (?, ?, ?)",
            (uid, filename, crop_type or "Unknown")
        )
        await db.commit()
        
        return {
            "success": True,
            "message": "✅ तस्वीर मिल गई! हम जल्द ही बीमारी पहचान की सुविधा शुरू करेंगे।"
        }
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        return {
            "success": False,
            "message": "❌ तस्वीर अपलोड नहीं हो सकी।"
        }


# ============================================================================
# 5. Onboarding
# ============================================================================

@router.post("/onboarding/location")
async def save_user_location(
    uid: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Save user GPS location"""
    try:
        loc_data = await weather_service.reverse_geocode(latitude, longitude)
        district = loc_data.get('district', 'Unknown')
        
        await db.execute("""
            INSERT INTO users (uid, lat, long, default_district, step)
            VALUES (?, ?, ?, ?, 'active')
            ON CONFLICT(uid) DO UPDATE SET
                lat = excluded.lat,
                long = excluded.long,
                default_district = excluded.default_district,
                updated_at = CURRENT_TIMESTAMP
        """, (uid, latitude, longitude, district))
        await db.commit()
        
        return {
            "success": True,
            "message": f"✅ लोकेशन सेव हो गई: {district}",
            "district": district
        }
    except Exception as e:
        logger.error(f"Location save error: {e}")
        return {
            "success": False,
            "message": "❌ लोकेशन सेव नहीं हो सकी।"
        }
