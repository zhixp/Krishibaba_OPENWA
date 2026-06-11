"""
Mandi Agent - Specialized for Market Price Analysis
Uses Gemini 1.5 Flash for quick market insights
"""
import google.generativeai as genai
from app.core.config import settings
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)


class MandiAgent:
    def __init__(self):
        self.model_name = "models/gemini-2.0-flash-exp"  # Fast & available
        
    async def analyze_prices(
        self,
        crop: str,
        prices: List[Dict],
        user_profile: str = ""
    ) -> str:
        """
        Analyze mandi prices and give market advice
        
        Args:
            crop: Crop name
            prices: List of price records from database
            user_profile: User's profile info
            
        Returns:
            2-3 line Hindi market advice
        """
        
        # Extract key info
        if not prices:
            return "कोई डेटा नहीं मिला।"
            
        highest_price = max(p.get('price_modal', 0) for p in prices[:5])
        lowest_price = min(p.get('price_modal', 0) for p in prices[:5])
        avg_price = sum(p.get('price_modal', 0) for p in prices[:5]) / len(prices[:5])
        
        prompt = f"""तुम मंडी विशेषज्ञ हो। किसानों को मार्केट की जानकारी देनी है।

फसल: {crop}

किसान की जानकारी:
{user_profile if user_profile else "सामान्य किसान"}

मंडी के भाव:
- सबसे ज्यादा: ₹{int(highest_price)}
- सबसे कम: ₹{int(lowest_price)}
- औसत: ₹{int(avg_price)}

कुल {len(prices)} मंडियों का डेटा

2-3 लाइन में सलाह दो:
- भाव अच्छे हैं या नहीं
- कहां बेचना सही रहेगा
- क्या इंतज़ार करना चाहिए

सीधी हिंदी में:"""

        try:
            logger.info(f"💰 Mandi Agent analyzing {crop} prices")
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Mandi Agent error: {e}")
            return f"{crop} के भाव ठीक चल रहे हैं। नज़दीकी मंडी में देखो।"


# Singleton
mandi_agent = MandiAgent()
