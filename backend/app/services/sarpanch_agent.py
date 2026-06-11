"""
Sarpanch AI Agent - Main Farming Advisor
Uses Gemini 1.5 Pro Latest for best reasoning
"""
import google.generativeai as genai
from app.core.config import settings
import logging
from typing import Dict

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)


class SarpanchAgent:
    def __init__(self):
        self.model_name = "models/gemini-2.5-pro"  # Best reasoning
        
    async def chat(
        self,
        message: str,
        user_profile: str = "",
        chat_history: str = ""
    ) -> str:
        """
        Main farming chat - general advice, problem solving
        
        Args:
            message: User's question
            user_profile: User info (crops, location, facts)
            chat_history: Last 20 messages
            
        Returns:
            Helpful Hindi farming advice
        """
        
        prompt = f"""तुम कृषि बाबा हो - किसानों के मददगार।

किसान की जानकारी:
{user_profile if user_profile else "नया किसान"}

पिछली बातचीत:
{chat_history if chat_history else "पहली बार बात"}

किसान का सवाल: "{message}"

IMPORTANT RULES:
1. Reply ONLY in simple Hindi
2. NO special formatting - no **, no bullets, no ---
3. Give direct, helpful farming advice
4. If asked about weather/prices: "Weather ke liye Weather section dekho. Mandi bhav ke liye Mandi section dekho."
5. Be concise and friendly

Give a simple, clear answer in plain Hindi:"""

        try:
            logger.info(f"🌾 Sarpanch AI answering: {message[:50]}...")
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            
            # Clean up any formatting
            clean_response = response.text.strip()
            clean_response = clean_response.replace('**', '')  # Remove bold
            clean_response = clean_response.replace('*', '')   # Remove italics
            
            return clean_response
            
        except Exception as e:
            logger.error(f"Sarpanch AI error: {e}")
            return "क्षमा करें, अभी जवाब नहीं दे सकता। थोड़ी देर बाद पूछो।"
    
    def is_greeting(self, text: str) -> bool:
        """Check if message is a greeting"""
        greetings = [
            'hello', 'hi', 'hey', 'namaste', 'namaskar',
            'ram ram', 'kaise ho', 'kya haal'
        ]
        text_lower = text.lower()
        return any(g in text_lower for g in greetings) and len(text.split()) <= 5


# Singleton
sarpanch_agent = SarpanchAgent()
