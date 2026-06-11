"""
Intent Classifier - Routes user queries to appropriate agents
Lightweight, keyword-based routing
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Determines which agents should handle the user's query
    Based on keyword matching - fast and reliable
    """
    
    def __init__(self):
        # Weather-related keywords
        self.weather_keywords = [
            'mausam', 'barish', 'weather', 'rain', 'baarish',
            'thand', 'garmi', 'cold', 'hot', 'sardi', 'गर्मी', 'ठंड',
            'aaj', 'kal', 'today', 'tomorrow', 'parso',
            'hawa', 'wind', 'dhoop', 'sun', 'badal', 'cloud',
            'humidity', 'nami', 'नमी'
        ]
        
        # Mandi/price-related keywords
        self.mandi_keywords = [
            'bhav', 'rate', 'price', 'mandi', 'मंडी', 'भाव',
            'bechna', 'sell', 'market', 'keemat', 'कीमत',
            'daam', 'दाम', 'beche', 'बेचे', 'बेचना',
            'modal', 'minimum', 'maximum', 'rupee', 'rupaye'
        ]
        
        # Decision-making keywords (often needs multiple agents)
        self.decision_keywords = [
            'jaun', 'जाऊं', 'should', 'chahiye', 'चाहिए',
            'karna', 'करना', 'करूं', 'karun'
        ]
    
    def classify(self, message: str, user_location: str = None) -> Dict[str, bool]:
        """
        Classify user intent and determine which agents to call
        
        Args:
            message: User's query
            user_location: User's location (for context)
            
        Returns:
            {
                "needs_weather": bool,
                "needs_mandi": bool,
                "needs_advice": bool,  # Sarpanch always runs
                "confidence": str       # low/medium/high
            }
        """
        msg_lower = message.lower()
        
        # Check for keywords
        has_weather = any(kw in msg_lower for kw in self.weather_keywords)
        has_mandi = any(kw in msg_lower for kw in self.mandi_keywords)
        has_decision = any(kw in msg_lower for kw in self.decision_keywords)
        
        # Decision questions often need both weather and mandi
        if has_decision and (has_weather or has_mandi):
            # Complex decision - fetch all data
            result = {
                "needs_weather": True,
                "needs_mandi": True,
                "needs_advice": True,
                "confidence": "high"
            }
            logger.info(f"🎯 Complex query detected: {message[:50]}... → Weather + Mandi + Advice")
        
        elif has_weather and has_mandi:
            # Both mentioned explicitly
            result = {
                "needs_weather": True,
                "needs_mandi": True,
                "needs_advice": True,
                "confidence": "high"
            }
            logger.info(f"🎯 Multi-topic query: {message[:50]}... → Weather + Mandi")
        
        elif has_weather:
            # Weather only
            result = {
                "needs_weather": True,
                "needs_mandi": False,
                "needs_advice": True,
                "confidence": "medium"
            }
            logger.info(f"🌦️ Weather query: {message[:50]}...")
        
        elif has_mandi:
            # Mandi only
            result = {
                "needs_weather": False,
                "needs_mandi": True,
                "needs_advice": True,
                "confidence": "medium"
            }
            logger.info(f"💰 Mandi query: {message[:50]}...")
        
        else:
            # General farming advice
            result = {
                "needs_weather": False,
                "needs_mandi": False,
                "needs_advice": True,
                "confidence": "low"
            }
            logger.info(f"🌾 General advice: {message[:50]}...")
        
        return result


# Singleton
intent_classifier = IntentClassifier()
