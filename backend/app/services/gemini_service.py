"""
Gemini Service - CLEAN VERSION
Simple, no hallucination, using Gemini 1.5 Pro
"""
import google.generativeai as genai
from app.core.config import settings
import logging
from typing import Dict, List
import re

logger = logging.getLogger(__name__)

API_KEY = settings.GEMINI_API_KEY
genai.configure(api_key=API_KEY)

# Use STABLE models only
MODEL_ROSTER = [
    'gemini-1.5-pro',
    'gemini-1.5-flash'
]


class GeminiService:
    def __init__(self):
        self.primary_model = "gemini-1.5-pro"
    
    async def _generate_response(self, prompt_text: str):
        """Internal helper with fallback"""
        for model_name in [self.primary_model] + MODEL_ROSTER:
            try:
                logger.info(f"🔄 Using {model_name}...")
                model = genai.GenerativeModel(model_name)
                result = model.generate_content(prompt_text)
                return result.text
            except Exception as e:
                logger.warning(f"⚠️ {model_name} failed: {e}")
                continue
        
        raise Exception("All models failed")
    
    # ========================================================================
    # WEATHER COMMENTARY
    # ========================================================================
    
    async def generate_weather_commentary(
        self, 
        forecast_data: List[Dict],
        location: str
    ) -> str:
        """Generate 2-3 line weather advice in Hindi"""
        import json
        
        prompt = f"""तुम कृषि सलाहकार हो। {location} का मौसम डेटा:

{json.dumps(forecast_data, indent=2, ensure_ascii=False)}

2-3 लाइन में खेती की सलाह दो (नमी, हवा, बारिश के आधार पर):"""
        
        try:
            response = await self._generate_response(prompt)
            return response.strip()
        except:
            return "मौसम के अनुसार खेती करें।"
    
    # ========================================================================
    # FARMING ADVICE - SIMPLE
    # ========================================================================
    
    async def generate_farming_advice(
        self, 
        message: str,
        user_context: Dict,
        chat_history: str = "",
        user_profile: str = ""
    ) -> str:
        """Give simple, clear farming advice"""
        
        prompt = f"""तुम कृषि बाबा हो।

किसान: {user_profile if user_profile else "नया किसान"}

पिछली बातचीत:
{chat_history if chat_history else "पहली बार"}

सवाल: "{message}"

नियम:
- सिर्फ खेती की सलाह
- सीधी, साफ हिंदी
- कोई मौसम/भाव मत बताओ

जवाब:"""
        
        try:
            response = await self._generate_response(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return "क्षमा करें, कुछ गड़बड़ हो गई।"
    
    # ========================================================================
    # GREETING DETECTION
    # ========================================================================
    
    def is_greeting(self, text: str) -> bool:
        """Quick check for greetings"""
        greetings = [
            'hello', 'hi', 'hey', 'namaste', 'namaskar',
            'ram ram', 'kaise ho', 'kya haal',
            'good morning', 'good evening'
        ]
        text_lower = text.lower()
        return any(g in text_lower for g in greetings) and len(text.split()) <= 5


# Singleton
gemini_service = GeminiService()
