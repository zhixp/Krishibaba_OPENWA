"""
Weather Service - OpenWeather + Hybrid Geocoding
🚨 OPTIMIZED FOR 2G NETWORKS - 3s timeout on all API calls
"""
import aiohttp
import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.core.config import settings
import asyncio

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for weather data and geocoding using OpenWeather API"""
    
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
        self.weather_url = "https://api.openweathermap.org/data/2.5/weather"
        self.forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        # 🚨 CRITICAL: 3-second timeout for 2G networks
        self.timeout = aiohttp.ClientTimeout(total=3)
        
        logger.info("🌤️ Weather Service initialized with 3s timeout (2G optimized)")
        
    async def geocode_location(self, location_query: str, country: str = "IN") -> Optional[Dict]:
        """
        Geocode ANY location query: pincode, village, town, district
        
        Args:
            location_query: Could be "464774" or "Udaipura" or "Raisen"
            country: Country code (default: IN)
            
        Returns:
            Dict with {lat, lon, location_name, state, district} or None
        """
        # Check if it's a pincode (6 digits)
        if location_query.strip().isdigit() and len(location_query.strip()) == 6:
            return await self.reverse_geocode_pincode(location_query, country)
        
        # Otherwise, treat as village/town/district name
        logger.info(f"🔍 Geocoding location name: {location_query}")
        
        # Try Google Maps first
        google_api_key = settings.GOOGLE_MAPS_API_KEY
        
        if google_api_key:
            try:
                google_url = "https://maps.googleapis.com/maps/api/geocode/json"
                
                async with aiohttp.ClientSession() as session:
                    params = {
                        "address": f"{location_query}, India",
                        "key": google_api_key
                    }
                    
                    async with session.get(google_url, params=params, timeout=aiohttp.ClientTimeout(total=3)) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get("status") == "OK" and data.get("results"):
                                location = data["results"][0]
                                geometry = location.get("geometry", {})
                                address_components = location.get("address_components", [])
                                
                                location_name = location_query.title()
                                state = "India"
                                district = "Unknown"
                                
                                for component in address_components:
                                    types = component.get("types", [])
                                    
                                    if "locality" in types:
                                        location_name = component.get("long_name", location_query)
                                    elif "administrative_area_level_2" in types:
                                        district = component.get("long_name", "Unknown")
                                    elif "administrative_area_level_1" in types:
                                        state = component.get("long_name", "India")
                                
                                lat = geometry.get("location", {}).get("lat")
                                lon = geometry.get("location", {}).get("lng")
                                
                                if lat and lon:
                                    result = {
                                        "lat": float(lat),
                                        "lon": float(lon),
                                        "location_name": location_name,
                                        "state": state,
                                        "district": district if district != "Unknown" else location_name
                                    }
                                    
                                    logger.info(f"✅ Google Maps: {location_query} → {location_name}, {state}")
                                    return result
                            
            except Exception as e:
                logger.warning(f"Google Maps geocoding failed: {e}, falling back to Nominatim")
        
        # Fallback: Nominatim
        try:
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": f"{location_query}, India",
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1
                }
                
                headers = {"User-Agent": "SarpanchAI/1.0"}
                
                async with session.get(nominatim_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and len(data) > 0:
                            location = data[0]
                            address = location.get("address", {})
                            
                            district = (
                                address.get("county") or
                                address.get("state_district") or
                                address.get("city") or
                                address.get("town") or
                                address.get("village") or
                                location_query.title()
                            )
                            
                            state = address.get("state", "India")
                            
                            result = {
                                "lat": float(location.get("lat")),
                                "lon": float(location.get("lon")),
                                "location_name": district,
                                "state": state,
                                "district": district
                            }
                            
                            logger.info(f"✅ Nominatim: {location_query} → {district}, {state}")
                            return result
                        
            logger.error(f"❌ No location found for: {location_query}")
            return None
                        
        except Exception as e:
            logger.error(f"Nominatim geocoding failed: {e}")
            return None
    
    async def reverse_geocode_pincode(self, pincode: str, country: str = "IN") -> Optional[Dict]:
        """
        Convert Indian pincode to lat/lon coordinates
        """
        try:
            logger.info(f"🔍 Geocoding pincode: {pincode}")
            
            # Use Nominatim (free)  
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                "postalcode": pincode,
                "country": country,
                "format": "json",
                "limit": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout, headers={"User-Agent": "KrishiBabaApp/1.0"}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and len(data) > 0:
                            result = {
                                "lat": float(data[0]["lat"]),
                                "lon": float(data[0]["lon"]),
                                "location_name": data[0].get("display_name", pincode),
                                "district": data[0].get("address", {}).get("state_district", "Unknown"),
                                "state": data[0].get("address", {}).get("state", "India")
                            }
                            logger.info(f"✅ Pincode {pincode} → {result['district']}")
                            return result
            
            return None
        except Exception as e:
            logger.error(f"Pincode geocoding failed: {e}")
            return None
    
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Reverse Geocode: Lat/Lon -> Location Name (District/Village)
        """
        # 1. Try Google Maps (Precise)
        google_api_key = settings.GOOGLE_MAPS_API_KEY
        if google_api_key:
            try:
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    "latlng": f"{lat},{lon}",
                    "key": google_api_key,
                    "language": "en"
                } 
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("results"):
                                res = data["results"][0]
                                location_name = "Unknown"
                                district = "Unknown"
                                state = "India"
                                
                                for comp in res.get("address_components", []):
                                    types = comp.get("types", [])
                                    if "locality" in types:
                                        location_name = comp["long_name"]
                                    elif "administrative_area_level_2" in types: # District
                                        district = comp["long_name"]
                                    elif "administrative_area_level_1" in types: # State
                                        state = comp["long_name"]
                                        
                                if district == "Unknown": district = location_name
                                
                                logger.info(f"📍 GPS Reverse Geocode: {district}, {state}")
                                return {
                                    "lat": lat, "lon": lon,
                                    "location_name": location_name,
                                    "district": district,
                                    "state": state
                                }
            except Exception as e:
                logger.warning(f"Google Reverse Geocode failed: {e}")

        # 2. Fallback: Nominatim (Free)
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": lat, "lon": lon,
                "format": "json",
                "zoom": 10
            }
            headers = {"User-Agent": "SarpanchAI/1.0"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        address = data.get("address", {})
                        district = address.get("state_district") or address.get("county") or address.get("city") or "Unknown"
                        state = address.get("state", "India")
                        
                        logger.info(f"📍 Nominatim Reverse Geocode: {district}, {state}")
                        return {
                            "lat": lat, "lon": lon,
                            "location_name": district,
                            "district": district,
                            "state": state
                        }
        except Exception as e:
            logger.error(f"Nominatim Reverse Geocode failed: {e}")
            
        return None
        """
        HYBRID GEOCODING: Google Maps (Primary) → Nominatim (Fallback)
        
        Tries Google Maps first for high accuracy, falls back to Nominatim if:
        - Google API key is missing
        - Google request fails
        - Quota is exceeded
        
        Args:
            pincode: 6-digit Indian pincode
            country: Country code (default: IN for India)
            
        Returns:
            Dict with {lat, lon, location_name, state, district} or None if not found
        """
        
        # ===================================================================
        # PRIMARY: Try Google Maps Geocoding (High Accuracy)
        # ===================================================================
        google_api_key = settings.GOOGLE_MAPS_API_KEY
        
        if google_api_key:
            try:
                logger.info(f"🔍 Trying Google Maps for pincode {pincode}...")
                
                google_url = "https://maps.googleapis.com/maps/api/geocode/json"
                
                async with aiohttp.ClientSession() as session:
                    params = {
                        "address": pincode,
                        "components": f"country:{country}",
                        "key": google_api_key
                    }
                    
                    async with session.get(google_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get("status") == "OK" and data.get("results"):
                                location = data["results"][0]
                                geometry = location.get("geometry", {})
                                address_components = location.get("address_components", [])
                                
                                # Extract precise location name
                                # Priority: locality (Village/Town) > administrative_area_level_2 (Tehsil)
                                location_name = "Unknown"
                                state = "India"
                                district = "Unknown"
                                
                                for component in address_components:
                                    types = component.get("types", [])
                                    
                                    # Get locality (most specific - village/town)
                                    if "locality" in types:
                                        location_name = component.get("long_name", "Unknown")
                                    
                                    # Get tehsil/district (fallback)
                                    elif "administrative_area_level_2" in types and location_name == "Unknown":
                                        district = component.get("long_name", "Unknown")
                                        location_name = district
                                    
                                    # Get state
                                    elif "administrative_area_level_1" in types:
                                        state = component.get("long_name", "India")
                                
                                # Extract coordinates
                                lat = geometry.get("location", {}).get("lat")
                                lon = geometry.get("location", {}).get("lng")
                                
                                if lat and lon:
                                    result = {
                                        "lat": float(lat),
                                        "lon": float(lon),
                                        "location_name": location_name,
                                        "state": state,
                                        "district": district if district != "Unknown" else location_name
                                    }
                                    
                                    logger.info(f"✅ Google Maps: {pincode} → {location_name}, {state}")
                                    return result
                            
                            elif data.get("status") == "OVER_QUERY_LIMIT":
                                logger.warning("⚠️ Google Maps quota exceeded, falling back to Nominatim")
                            else:
                                logger.warning(f"Google Maps returned status: {data.get('status')}")
                        
                        else:
                            logger.warning(f"Google Maps API error: {response.status}")
                            
            except Exception as e:
                logger.warning(f"Google Maps failed: {e}, falling back to Nominatim")
        
        else:
            logger.info("ℹ️ Google Maps API key not configured, using Nominatim")
        
        # ===================================================================
        # FALLBACK: Nominatim (OpenStreetMap) - Always Available
        # ===================================================================
        try:
            logger.info(f"🔍 Using Nominatim fallback for pincode {pincode}...")
            
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "postalcode": pincode,
                    "country": "India",
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1
                }
                
                headers = {
                    "User-Agent": "SarpanchAI/1.0"
                }
                
                async with session.get(nominatim_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and len(data) > 0:
                            location = data[0]
                            address = location.get("address", {})
                            
                            # Extract location info
                            district = (
                                address.get("county") or
                                address.get("state_district") or
                                address.get("city") or
                                address.get("town") or
                                address.get("village") or
                                "Unknown"
                            )
                            
                            state = address.get("state", "India")
                            
                            result = {
                                "lat": float(location.get("lat")),
                                "lon": float(location.get("lon")),
                                "location_name": district,
                                "state": state,
                                "district": district
                            }
                            
                            logger.info(f"✅ Nominatim: {pincode} → {district}, {state}")
                            return result
                        
                        else:
                            logger.error(f"❌ No location found for pincode: {pincode}")
                            return None
                    
                    else:
                        logger.error(f"Nominatim API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Nominatim geocoding failed: {e}")
            return None
    
    async def get_current_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get current weather for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict with weather data or None if error
        """
        """
        Get current weather with 3-second timeout
        🚨 Returns None if API slow - better than 20s hang
        """
        if not self.api_key:
            logger.error("OpenWeather API key not configured")
            return None
            
        endpoint = f"{self.base_url}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "hi"
        }
        
        try:
            # 🚨 3-SECOND TIMEOUT - Abort if slow
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract relevant data
                        weather = {
                            "temp": data["main"]["temp"],
                            "feels_like": data["main"]["feels_like"],
                            "temp_min": data["main"]["temp_min"],
                            "temp_max": data["main"]["temp_max"],
                            "humidity": data["main"]["humidity"],
                            "description": data["weather"][0]["description"],
                            "main": data["weather"][0]["main"],
                            "icon": data["weather"][0]["icon"],
                            "wind_speed": data["wind"]["speed"],
                            "clouds": data["clouds"]["all"],
                            "location": data.get("name", "Unknown")
                        }
                        
                        # Add rain data if available
                        if "rain" in data:
                            weather["rain_1h"] = data["rain"].get("1h", 0)
                            weather["rain_3h"] = data["rain"].get("3h", 0)
                        
                        logger.info(f"✅ Got current weather for {weather['location']}: {weather['temp']}°C")
                        return weather
                    else:
                        logger.error(f"Weather API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return None
    
    async def get_forecast(self, lat: float, lon: float, days: int = 3) -> Optional[List[Dict]]:
        """
        Get weather forecast for next N days
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days (max 5 for free tier)
            
        Returns:
            List of forecast dicts or None if error
        """
        if not self.api_key:
            logger.error("OpenWeather API key not configured")
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric",
                    "lang": "hi",
                    "cnt": days * 8  # API gives 3-hour intervals, 8 per day
                }
                
                async with session.get(self.forecast_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Group by day and extract key info
                        daily_forecasts = []
                        seen_dates = set()
                        
                        for item in data["list"]:
                            date = datetime.fromtimestamp(item["dt"]).date()
                            
                            # Only take one forecast per day (noon forecast)
                            if date not in seen_dates:
                                forecast = {
                                    "date": date.isoformat(),
                                    "temp": item["main"]["temp"],
                                    "temp_min": item["main"]["temp_min"],
                                    "temp_max": item["main"]["temp_max"],
                                    "description": item["weather"][0]["description"],
                                    "main": item["weather"][0]["main"],
                                    "humidity": item["main"]["humidity"],
                                    "wind_speed": item["wind"]["speed"]
                                }
                                
                                # Add rain probability if available
                                if "rain" in item:
                                    forecast["rain_mm"] = item["rain"].get("3h", 0)
                                
                                if "pop" in item:  # Probability of precipitation
                                    forecast["rain_probability"] = item["pop"] * 100
                                
                                daily_forecasts.append(forecast)
                                seen_dates.add(date)
                                
                                if len(daily_forecasts) >= days:
                                    break
                        
                        logger.info(f"✅ Got {len(daily_forecasts)}-day forecast")
                        return daily_forecasts
                    else:
                        logger.error(f"Forecast API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return None
    
    def format_weather_for_ai(self, weather_data: Dict) -> str:
        """Format weather data for AI prompt"""
        if not weather_data:
            return "Weather data not available"
        
        text = f"Temperature: {weather_data['temp']}°C (feels like {weather_data['feels_like']}°C)\n"
        text += f"Condition: {weather_data['description']}\n"
        text += f"Humidity: {weather_data['humidity']}%\n"
        text += f"Wind: {weather_data['wind_speed']} m/s\n"
        
        if "rain_1h" in weather_data and weather_data["rain_1h"] > 0:
            text += f"Rain (last hour): {weather_data['rain_1h']}mm\n"
        
        return text
    
    def format_forecast_for_ai(self, forecast: List[Dict]) -> str:
        """Format forecast data for AI prompt"""
        if not forecast:
            return "Forecast not available"
        
        text = "Next 3 days forecast:\n"
        for day in forecast:
            text += f"\n{day['date']}: {day['temp']}°C, {day['description']}"
            if "rain_probability" in day:
                text += f" (Rain chance: {day['rain_probability']:.0f}%)"
        
        return text
    
    async def get_weather_summary_3days(self, lat: float, lon: float) -> Optional[str]:
        """
        Get 3-day weather summary for AI consumption
        Returns formatted Hindi text ready for direct use
        """
        try:
            # Get current weather
            current = await self.get_current_weather(lat, lon)
            if not current:
                return None
            
            # Get forecast
            forecast = await self.get_forecast(lat, lon, days=3)
            if not forecast:
                return None
            
            # Format for Hindi output
            from datetime import datetime
            
            summary = f"📍 {current.get('location', 'आपके क्षेत्र')}\n\n"
            summary += f"**आज ({datetime.now().strftime('%d %b')}):**\n"
            summary += f"🌡️ {current.get('temp', 'N/A')}°C - {current.get('description', '')}\n"
            summary += f"💧 नमी: {current.get('humidity', 'N/A')}%\n\n"
            
            summary += "**अगले 3 दिन:**\n"
            
            for i, day in enumerate(forecast[:3], 1):
                summary += f"\n**{day.get('date', '')}:**\n"
                summary += f"🌡️ {day.get('temp', '')}°C - {day.get('description', '')}\n"
                
                if 'rain_probability' in day and day['rain_probability'] > 30:
                    summary += f"☔ बारिश: {day['rain_probability']:.0f}% संभावना\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Weather summary error: {e}")
            return None


# Global weather service instance
weather_service = WeatherService()

