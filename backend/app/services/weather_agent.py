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
        Analyze 3-day forecast and give farming advice
        
        Args:
            forecast_data: Weather data from OpenWeatherMap
            location: Location name
            user_profile: User's profile info (crops, location)
            
        Returns:
            3-4 line Hindi weather advice for farming
        """
        
        prompt = f"""तुम मौसम विशेषज्ञ हो। किसानों को मौसम के आधार पर सलाह देनी है।

स्थान: {location}

किसान की जानकारी:
{user_profile if user_profile else "सामान्य किसान"}

3 दिन का मौसम डेटा:
{json.dumps(forecast_data, indent=2, ensure_ascii=False)}

3-4 लाइन में सलाह दो:
- नमी (Humidity) का असर
- हवा (Wind) की स्थिति
- बारिश की संभावना
- इसके हिसाब से खेती के काम

सीधी, साफ हिंदी में जवाब:"""

        try:
            logger.info(f"🌦️ Weather Agent analyzing forecast for {location}")
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Weather Agent error: {e}")
            return "मौसम साफ है। सामान्य खेती के काम कर सकते हो।"


# Singleton
weather_agent = WeatherAgent()
