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
from app.services.location_service import (
    LOCATION_ONBOARDING_MESSAGE,
    build_weather_location_from_user,
    resolve_onboarding_location,
    weather_location_note,
)
from app.core.config import settings
from app.core.security import redacted_identifier
from app.core.uploads import ALLOWED_IMAGE_MIME_TYPES, ALLOWED_IMAGE_SUFFIXES, save_bounded_upload
import aiosqlite
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["Sarpanch AI"])


async def _save_resolved_location(
    db: aiosqlite.Connection,
    uid: str,
    resolved: dict,
) -> None:
    await db.execute("""
        INSERT INTO users
        (uid, lat, long, gps_lat, gps_lon, default_pincode, village,
         default_district, state, location_source, location_confidence,
         location_data, step)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        ON CONFLICT(uid) DO UPDATE SET
            lat = excluded.lat,
            long = excluded.long,
            gps_lat = excluded.gps_lat,
            gps_lon = excluded.gps_lon,
            default_pincode = COALESCE(excluded.default_pincode, users.default_pincode),
            village = COALESCE(excluded.village, users.village),
            default_district = COALESCE(excluded.default_district, users.default_district),
            state = COALESCE(excluded.state, users.state),
            location_source = excluded.location_source,
            location_confidence = excluded.location_confidence,
            location_data = excluded.location_data,
            updated_at = CURRENT_TIMESTAMP
    """, (
        uid,
        resolved["lat"],
        resolved["lon"],
        resolved.get("gps_lat"),
        resolved.get("gps_lon"),
        resolved.get("pincode"),
        resolved.get("village"),
        resolved.get("district"),
        resolved.get("state"),
        resolved["location_source"],
        resolved["location_confidence"],
        json.dumps(resolved.get("location_data") or {}, ensure_ascii=False),
    ))
    await db.commit()


# ============================================================================
# 1. WEATHER AGENT - Forecast Analysis
# ============================================================================

@router.post("/weather/report")
async def get_weather_report(
    uid: str = Form(...),
    latitude: Optional[float] = Form(None, ge=-90, le=90),
    longitude: Optional[float] = Form(None, ge=-180, le=180),
    pincode: Optional[str] = Form(None),
    village: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Weather Agent: 3-day forecast with explicit location confidence.
    """
    try:
        cursor = await db.execute(
            """SELECT lat, long, gps_lat, gps_lon, default_pincode, default_district,
                      village, state, location_source, location_confidence
               FROM users WHERE uid = ?""",
            (uid,),
        )
        row = await cursor.fetchone()
        user_location_data = dict(row) if row else {}
        saved_location = build_weather_location_from_user(user_location_data) if row else None
        has_text_location_input = any([pincode, village, district, state])

        # Fresh GPS from WhatsApp always wins and upgrades approximate saved locations.
        if latitude is not None or longitude is not None:
            resolved = await resolve_onboarding_location(
                latitude=latitude,
                longitude=longitude,
                pincode=pincode,
                village=village,
                district=district,
                state=state,
            )
            if not resolved.get("success"):
                return {
                    "success": False,
                    "needs_location": True,
                    "message": resolved.get("message") or LOCATION_ONBOARDING_MESSAGE,
                }

            await _save_resolved_location(db, uid, resolved)
            location_context = {
                "lat": resolved["lat"],
                "lon": resolved["lon"],
                "source": resolved["location_source"],
                "confidence": resolved["location_confidence"],
                "display_name": resolved.get("location_name") or resolved.get("district") or "आपकी लोकेशन",
            }
        elif saved_location and saved_location["source"] == "gps":
            location_context = saved_location
        else:
            resolved = await resolve_onboarding_location(
                pincode=pincode or (None if has_text_location_input else user_location_data.get("default_pincode")),
                village=village or (None if has_text_location_input else user_location_data.get("village")),
                district=district or (None if has_text_location_input else user_location_data.get("default_district")),
                state=state or (None if has_text_location_input else user_location_data.get("state")),
            )
            if not resolved.get("success"):
                if saved_location:
                    location_context = saved_location
                else:
                    return {
                        "success": False,
                        "needs_location": True,
                        "message": resolved.get("message") or LOCATION_ONBOARDING_MESSAGE,
                    }
            else:
                location_context = {
                    "lat": resolved["lat"],
                    "lon": resolved["lon"],
                    "source": resolved["location_source"],
                    "confidence": resolved["location_confidence"],
                    "display_name": resolved.get("location_name") or resolved.get("district") or "आपका क्षेत्र",
                }

                await _save_resolved_location(db, uid, resolved)

        lat, lon = location_context["lat"], location_context["lon"]
        display_name = location_context["display_name"]
        source = location_context["source"]
        confidence = location_context["confidence"]
        
        # Fetch weather data
        current = await weather_service.get_current_weather(lat, lon)
        forecast = await weather_service.get_forecast(lat, lon, days=5)
        
        if not current or not forecast:
            return {
                "success": False,
                "message": "❌ मौसम का डेटा नहीं मिल सका। बाद में कोशिश करें।"
            }
        
        # Get user profile for personalized advice
        profile_context = await user_profile.get_formatted_context(db, uid)
        
        # WEATHER AGENT: Analyze forecast
        weather_advice = await weather_agent.analyze_forecast(
            forecast_data=forecast[:3],
            location=display_name,
            user_profile=profile_context
        )

        later_rain_note = None
        for day in forecast[3:]:
            rain_probability = day.get("rain_probability", 0) or 0
            rain_mm = day.get("rain_mm", 0) or 0
            if rain_probability >= 30 or rain_mm > 0:
                later_rain_note = (
                    f"{day.get('date')} को बारिश की संभावना दिख रही है। "
                    "लंबा forecast बदल सकता है, 2-3 दिन बाद फिर चेक कर लेना।"
                )
                break
        
        return {
            "success": True,
            "location": f"📍 {display_name}",
            "weather_location_note": weather_location_note(source),
            "location_source": source,
            "location_confidence": confidence,
            "approximate_location": source != "gps",
            "generated_at": datetime.now().isoformat(),
            "current": {
                "temp": f"{current.get('temp')}°C",
                "condition": current.get('description'),
                "humidity": f"{current.get('humidity')}%",
                "wind_speed": current.get("wind_speed"),
                "icon": current.get('icon')
            },
            "forecast": [
                {
                    "date": day.get('date'),
                    "temp_min": day.get('temp_min'),
                    "temp_max": day.get('temp_max'),
                    "condition": day.get('description'),
                    "rain_chance": f"{day.get('rain_probability', 0)}%",
                    "humidity": day.get("humidity"),
                    "wind_speed": day.get("wind_speed"),
                    "icon": day.get('icon')
                }
                for day in forecast[:3]
            ],
            "later_rain_note": later_rain_note,
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
    file_path: Optional[Path] = None
    try:
        filename, file_path, file_size = await save_bounded_upload(
            upload=image,
            destination_dir=Path("uploads/images"),
            owner_id=uid,
            allowed_mime_types=ALLOWED_IMAGE_MIME_TYPES,
            allowed_suffixes=ALLOWED_IMAGE_SUFFIXES,
            max_size_mb=max(1, settings.MAX_IMAGE_SIZE_MB),
        )

        logger.info(
            "Disease image saved for uid_hash=%s bytes=%s",
            redacted_identifier(uid),
            file_size,
        )
        
        await db.execute(
            "INSERT INTO uploaded_images (uid, filename, crop_type, file_size) VALUES (?, ?, ?, ?)",
            (uid, filename, crop_type or "Unknown", file_size)
        )
        await db.commit()
        
        return {
            "success": True,
            "message": "✅ तस्वीर मिल गई! हम जल्द ही बीमारी पहचान की सुविधा शुरू करेंगे।"
        }
    except Exception as e:
        if file_path and file_path.exists():
            file_path.unlink()
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
    latitude: Optional[float] = Form(None, ge=-90, le=90),
    longitude: Optional[float] = Form(None, ge=-180, le=180),
    pincode: Optional[str] = Form(None),
    village: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Save GPS-first location, with pincode or village+district as fallback."""
    try:
        resolved = await resolve_onboarding_location(
            latitude=latitude,
            longitude=longitude,
            pincode=pincode,
            village=village,
            district=district,
            state=state,
        )

        if not resolved.get("success"):
            return {
                "success": False,
                "needs_location": resolved.get("needs_location", False),
                "needs_district": resolved.get("needs_district", False),
                "message": resolved.get("message") or LOCATION_ONBOARDING_MESSAGE,
            }
        
        await _save_resolved_location(db, uid, resolved)
        
        return {
            "success": True,
            "message": resolved["message"],
            "location_source": resolved["location_source"],
            "location_confidence": resolved["location_confidence"],
            "approximate_location": resolved["location_source"] != "gps",
            "pincode": resolved.get("pincode"),
            "village": resolved.get("village"),
            "district": resolved.get("district"),
            "state": resolved.get("state"),
        }
    except Exception as e:
        logger.error(f"Location save error: {e}")
        return {
            "success": False,
            "message": "❌ लोकेशन सेव नहीं हो सकी।"
        }
