"""
Weather Agent - Specialized for Weather Analysis
Uses Gemini 1.5 Flash for fast, focused weather commentary
"""
import google.generativeai as genai
from app.core.config import settings
import logging
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)


class WeatherAgent:
    def __init__(self):
        self.model_name = "models/gemini-2.0-flash-exp"  # Fast & available
        
    async def analyze_forecast(
        self,
        forecast_data: List[Dict],
        location: str,
        user_profile: str = ""
    ) -> str:
        """
        Analyze 3-day forecast without giving irrigation advice.
        
        Args:
            forecast_data: Weather data from OpenWeatherMap
            location: Location name
            user_profile: User's profile info (crops, location)
            
        Returns:
            3-4 line Hindi weather advice for farming
        """
        
        prompt = f"""तुम Krishi Baba के मौसम सहायक हो। किसान को सिर्फ मौसम forecast समझाना है।

स्थान: {location}

किसान की जानकारी:
{user_profile if user_profile else "सामान्य किसान"}

3 दिन का मौसम डेटा:
{json.dumps(forecast_data, indent=2, ensure_ascii=False)}

3-4 लाइन में सिर्फ forecast समझाओ:
- बारिश की संभावना
- तापमान
- नमी (Humidity)
- हवा (Wind)

सिंचाई, दवाई, छिड़काव, कटाई या खेत का काम करने/न करने की सलाह मत दो।
अगर किसान ने irrigation अलग से पूछा हो तभी field condition पूछी जाएगी; यहाँ नहीं।

सीधी, साफ हिंदी में जवाब:"""

        try:
            logger.info(f"🌦️ Weather Agent analyzing forecast for {location}")
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Weather Agent error: {e}")
            return "मौसम का छोटा सार नहीं बन पाया। ऊपर दिए 3 दिन के forecast को देखकर फैसला करें।"


# Singleton
weather_agent = WeatherAgent()
