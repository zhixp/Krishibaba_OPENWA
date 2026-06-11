"""
Unified Chat Router - "One Window, Three Brains"
Single endpoint that intelligently routes to specialists and synthesizes results
"""
from fastapi import APIRouter, Depends, Form
from app.database.db import get_db
from app.services.intent_classifier import intent_classifier
from app.services.weather_agent import weather_agent
from app.services.mandi_agent import mandi_agent
from app.services.sarpanch_agent import sarpanch_agent
from app.services.weather_service import weather_service
from app.services.chat_memory import chat_memory
from app.services.user_profile import user_profile
import aiosqlite
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/unified", tags=["Unified Chat"])


@router.post("/chat")
async def unified_chat(
    uid: str = Form(...),
    message: str = Form(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    UNIFIED CHAT: One Window, Three Brains
    
    Flow:
    1. Classify intent (what does user need?)
    2. Fetch data in parallel (weather/mandi if needed)
    3. Sarpanch synthesizes final answer with context
    
    Returns natural, context-aware response
    """
    try:
        logger.info(f"💬 Unified Chat: {message[:100]}...")
        
        # Get user profile
        profile = await user_profile.get_profile(db, uid)
        profile_context = await user_profile.get_formatted_context(db, uid)
        
        # Get chat history
        chat_history = await chat_memory.get_formatted_history(db, uid, limit=20)
        
        # STEP 1: Classify Intent
        intent = intent_classifier.classify(message, profile.get('location'))
        logger.info(f"🎯 Intent: {intent}")
        
        # STEP 2: Fetch Data (Parallel Execution)
        weather_data = None
        mandi_data = None
        
        tasks = []
        
        if intent['needs_weather']:
            # Prepare weather fetch task
            async def fetch_weather():
                try:
                    lat, lon = profile.get('lat'), profile.get('long')
                    if not lat or not lon:
                        return None
                    
                    current = await weather_service.get_current_weather(lat, lon)
                    forecast = await weather_service.get_forecast(lat, lon, days=3)
                    
                    if not current or not forecast:
                        return None
                    
                    # Get Weather Agent analysis
                    analysis = await weather_agent.analyze_forecast(
                        forecast_data=forecast,
                        location=profile.get('location', 'Unknown'),
                        user_profile=profile_context
                    )
                    
                    return {
                        "current": current,
                        "forecast": forecast,
                        "analysis": analysis
                    }
                except Exception as e:
                    logger.error(f"Weather fetch error: {e}")
                    return None
            
            tasks.append(("weather", fetch_weather()))
        
        if intent['needs_mandi']:
            # Prepare mandi fetch task
            async def fetch_mandi():
                try:
                    # Extract crop from user profile or message
                    user_crops = profile.get('crops', [])
                    crop = user_crops[0] if user_crops else "Wheat"  # Default
                    
                    # Try to extract crop from message
                    message_lower = message.lower()
                    common_crops = ['wheat', 'गेहूं', 'paddy', 'धान', 'soybean', 'सोयाबीन', 'cotton', 'कपास']
                    for c in common_crops:
                        if c in message_lower:
                            crop = c
                            break
                    
                    # Query database
                    query = """
                        SELECT crop, mandi, price_modal, price_min, price_max,
                               source_date, state, district
                        FROM mandi_price_history
                        WHERE crop LIKE ?
                        ORDER BY source_date DESC LIMIT 10
                    """
                    cursor = await db.execute(query, [f"%{crop}%"])
                    rows = await cursor.fetchall()
                    
                    if not rows:
                        return None
                    
                    prices = [{
                        "crop": row[0],
                        "mandi": row[1],
                        "price_modal": int(row[2]),
                        "min_price": int(row[3]) if row[3] else 0,
                        "max_price": int(row[4]) if row[4] else 0,
                        "date": row[5]
                    } for row in rows]
                    
                    # Get Mandi Agent analysis
                    analysis = await mandi_agent.analyze_prices(
                        crop=crop,
                        prices=prices,
                        user_profile=profile_context
                    )
                    
                    return {
                        "crop": crop,
                        "prices": prices,
                        "analysis": analysis
                    }
                except Exception as e:
                    logger.error(f"Mandi fetch error: {e}")
                    return None
            
            tasks.append(("mandi", fetch_mandi()))
        
        # Execute tasks in parallel
        if tasks:
            results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            
            for i, (task_name, _) in enumerate(tasks):
                if task_name == "weather":
                    weather_data = results[i] if not isinstance(results[i], Exception) else None
                elif task_name == "mandi":
                    mandi_data = results[i] if not isinstance(results[i], Exception) else None
        
        # STEP 3: Sarpanch Synthesis
        # Build context with fetched data
        data_context = ""
        
        if weather_data:
            data_context += f"\n\n=== मौसम की जानकारी ===\n{weather_data['analysis']}\n"
        
        if mandi_data:
            highest = max(mandi_data['prices'], key=lambda x: x['price_modal'])
            lowest = min(mandi_data['prices'], key=lambda x: x['price_modal'])
            data_context += f"\n\n=== मंडी के भाव ({mandi_data['crop']}) ===\n"
            data_context += f"सबसे ज्यादा: {highest['mandi']} में ₹{highest['price_modal']}\n"
            data_context += f"सबसे कम: {lowest['mandi']} में ₹{lowest['price_modal']}\n"
            data_context += f"सलाह: {mandi_data['analysis']}\n"
        
        # Check if greeting
        if sarpanch_agent.is_greeting(message):
            reply = f"राम राम {profile['name']}! 🙏\n\nक्या समस्या है? पूछो भैया।"
        else:
            # Enhanced context for Sarpanch
            enhanced_profile = profile_context
            if data_context:
                enhanced_profile += data_context
            
            # Get Sarpanch's final answer
            reply = await sarpanch_agent.chat(
                message=message,
                user_profile=enhanced_profile,
                chat_history=chat_history
            )
        
        # Save to memory
        await chat_memory.save_message(db, uid, "user", message)
        await chat_memory.save_message(db, uid, "assistant", reply)
        
        return {
            "success": True,
            "reply": reply,
            "intent": intent,  # For debugging
            "data_fetched": {
                "weather": weather_data is not None,
                "mandi": mandi_data is not None
            }
        }
    
    except Exception as e:
        logger.error(f"Unified chat error: {e}", exc_info=True)
        return {
            "success": False,
            "reply": "❌ कुछ गड़बड़ हो गई। बाद में कोशिश करें।"
        }
