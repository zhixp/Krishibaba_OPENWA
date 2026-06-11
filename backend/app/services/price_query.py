"""
Price Query Service
Handles querying price history with staleness detection
INCLUDES supply signal logic (Heavy Supply vs Shortage)
NEVER scrapes on user request - only reads from database
"""
from typing import Dict, Optional, List
from datetime import datetime, date
import aiosqlite
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.geo_utils import haversine_distance

logger = logging.getLogger(__name__)


class PriceQueryService:
    """Service for querying price history with staleness detection"""
    
    @staticmethod
    async def get_latest_price(
        db: aiosqlite.Connection,
        crop: str,
        mandi: str = None,
        location: str = None
    ) -> Optional[Dict]:
        """
        Get latest price from history with staleness check
        
        Args:
            db: Database connection
            crop: Crop name
            mandi: Specific mandi name (optional)
            location: General location (district/city) (optional)
        
        Returns:
            Dict with price data and staleness info, or None if not found
        """
        try:
            # Build query based on available filters
            if mandi:
                query = """
                    SELECT crop, mandi, price_modal, price_min, price_max,
                           source_date, scraped_at, state, district,
                           traded_quantity, arrivals_quantity, arrival_tonnes
                    FROM mandi_price_history
                    WHERE crop LIKE ? AND mandi LIKE ?
                    ORDER BY source_date DESC
                    LIMIT 1
                """
                params = (f"%{crop}%", f"%{mandi}%")
            elif location:
                # Search by location (mandi name or district)
                query = """
                    SELECT crop, mandi, price_modal, price_min, price_max,
                           source_date, scraped_at, state, district,
                           traded_quantity, arrivals_quantity, arrival_tonnes
                    FROM mandi_price_history
                    WHERE crop LIKE ? AND (mandi LIKE ? OR district LIKE ?)
                    ORDER BY source_date DESC
                    LIMIT 1
                """
                params = (f"%{crop}%", f"%{location}%", f"%{location}%")
            else:
                # Just crop, get any mandi
                query = """
                    SELECT crop, mandi, price_modal, price_min, price_max,
                           source_date, scraped_at, state, district,
                           traded_quantity, arrivals_quantity, arrival_tonnes
                    FROM mandi_price_history
                    WHERE crop LIKE ?
                    ORDER BY source_date DESC
                    LIMIT 1
                """
                params = (f"%{crop}%",)
            
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            
            if not row:
                logger.warning(f"No price history found for {crop} in {mandi or location}")
                return None
            
            # Convert to dict
            price_data = dict(row)
            
            # Calculate staleness
            source_date_str = price_data['source_date']
            source_date_obj = datetime.strptime(source_date_str, "%Y-%m-%d").date()
            today = date.today()
            days_old = (today - source_date_obj).days
            
            # Determine freshness status
            if days_old == 0:
                status = "fresh"
                status_hindi = "ताज़ा भाव"
            elif days_old == 1:
                status = "yesterday"
                status_hindi = "कल का भाव"
            elif days_old <= 7:
                status = "this_week"
                status_hindi = f"{days_old} दिन पुराना"
            else:
                status = "stale"
                status_hindi = f"{days_old} दिन पुराना"
            
            # Add staleness metadata
            price_data['is_stale'] = days_old > 0
            price_data['days_old'] = days_old
            price_data['freshness_status'] = status
            price_data['freshness_hindi'] = status_hindi
            
            # Format date for display
            price_data['date_display'] = source_date_obj.strftime("%d %b")
            
            logger.info(f"Found price for {crop}: ₹{price_data['price_modal']} ({status}, {days_old} days old)")
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error querying price: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_price_movement(
        db: aiosqlite.Connection,
        crop: str,
        mandi: str,
        days_back: int = 7
    ) -> Optional[Dict]:
        """
        Calculate price movement over time
        
        Args:
            db: Database connection
            crop: Crop name
            mandi: Mandi name
            days_back: How many days to look back
        
        Returns:
            Dict with price movement info (delta, percentage, trend)
        """
        try:
            # Get last 2 prices
            query = """
                SELECT price_modal, source_date
                FROM mandi_price_history
                WHERE crop LIKE ? AND mandi LIKE ?
                ORDER BY source_date DESC
                LIMIT 2
            """
            
            cursor = await db.execute(query, (f"%{crop}%", f"%{mandi}%"))
            rows = await cursor.fetchall()
            
            if len(rows) < 2:
                return None
            
            latest = dict(rows[0])
            previous = dict(rows[1])
            
            # Calculate delta
            price_delta = latest['price_modal'] - previous['price_modal']
            price_percentage = (price_delta / previous['price_modal']) * 100
            
            # Determine trend
            if price_delta > 0:
                trend = "up"
                trend_hindi = "बढ़ा"
                emoji = "📈"
            elif price_delta < 0:
                trend = "down"
                trend_hindi = "घटा"
                emoji = "📉"
            else:
                trend = "stable"
                trend_hindi = "स्थिर"
                emoji = "➡️"
            
            return {
                "current_price": latest['price_modal'],
                "previous_price": previous['price_modal'],
                "delta": price_delta,
                "percentage": price_percentage,
                "trend": trend,
                "trend_hindi": trend_hindi,
                "emoji": emoji,
                "message_hindi": f"{emoji} पिछली बार से ₹{abs(int(price_delta))} {trend_hindi}"
            }
            
        except Exception as e:
            logger.error(f"Error calculating price movement: {e}")
            return None
    
    @staticmethod
    async def get_supply_signal(
        db: aiosqlite.Connection,
        crop: str,
        state: str = "Madhya Pradesh"
    ) -> Optional[Dict]:
        """
        Calculate supply signal (Heavy Supply vs Shortage)
        Based on: Current arrival vs last week average
        
        Args:
            db: Database connection
            crop: Crop name
            state: State name
        
        Returns:
            Dict with signal, message_hindi, current_arrival, avg_arrival
        """
        try:
            # Get current arrival (most recent)
            query_current = """
                SELECT arrival_tonnes FROM mandi_price_history
                WHERE crop LIKE ? AND state LIKE ?
                ORDER BY source_date DESC, scraped_at DESC
                LIMIT 1
            """
            cursor = await db.execute(query_current, (f"%{crop}%", f"%{state}%"))
            current_row = await cursor.fetchone()
            
            if not current_row or not current_row[0]:
                return None
            
            current_arrival = current_row[0]
            
            # Get last week average
            query_avg = """
                SELECT AVG(arrival_tonnes) FROM mandi_price_history
                WHERE crop LIKE ? AND state LIKE ?
                AND source_date >= date('now', '-7 days')
                AND arrival_tonnes > 0
            """
            cursor = await db.execute(query_avg, (f"%{crop}%", f"%{state}%"))
            avg_row = await cursor.fetchone()
            
            if not avg_row or not avg_row[0]:
                return None
            
            avg_arrival = avg_row[0]
            
            # Calculate signal
            threshold = 0.20  # 20%
            
            if current_arrival > avg_arrival * (1 + threshold):
                signal = "heavy_supply"
                message_hindi = "🚜 भारी आवक - मंडी में माल ज़्यादा है"
            elif current_arrival < avg_arrival * (1 - threshold):
                signal = "shortage"
                message_hindi = "⚠️ माल कम है - मांग ज़्यादा हो सकती है"
            else:
                signal = "normal"
                message_hindi = "✅ सामान्य आवक"
            
            return {
                "signal": signal,
                "message_hindi": message_hindi,
                "current_arrival": current_arrival,
                "avg_arrival": avg_arrival
            }
            
        except Exception as e:
            logger.error(f"Error calculating supply signal: {e}")
            return None
    
    @staticmethod
    async def get_price_with_context(
        db: aiosqlite.Connection,
        crop: str,
        state: str = "Madhya Pradesh",
        mandi: str = None
    ) -> Optional[Dict]:
        """
        Get price with full context: staleness, movement, supply signal
        This is the complete package for AI responses
        """
        # Get basic price
        price_data = await PriceQueryService.get_latest_price(db, crop, mandi)
        if not price_data:
            return None
        
        # Price movement
        movement = await PriceQueryService.get_price_movement(
            db, crop, price_data['mandi']
        )
        if movement:
            price_data["price_movement"] = movement
        
        # Supply signal
        supply = await PriceQueryService.get_supply_signal(db, crop, state)
        if supply:
            price_data["supply_signal"] = supply
        
        return price_data
    
    @staticmethod
    async def get_prices_within_radius(
        db: aiosqlite.Connection,
        crop: str,
        user_lat: float,
        user_lon: float,
        radius_km: int = 100,
        max_results: int = 5
    ) -> Optional[List[Dict]]:
        """
        Get prices from all mandis within radius of user's GPS location
        
        Use Case: User asks "gehu ka mandi bhav" without specifying mandi
        → Show prices from all mandis within 100km
        
        Args:
            db: Database connection
            crop: Crop name
            user_lat: User's GPS latitude
            user_lon: User's GPS longitude
            radius_km: Search radius in kilometers (default: 100km)
            max_results: Maximum number of mandis to return (default: 5)
            
        Returns:
            List of price dicts sorted by distance, or None if no matches
        """
        try:
            # Get all latest prices for this crop in the state
            query = """
                SELECT DISTINCT crop, mandi, price_modal, price_min, price_max,
                       source_date, scraped_at, state, district,
                       traded_quantity, arrivals_quantity, arrival_tonnes
                FROM mandi_price_history
                WHERE crop LIKE ? AND state = 'Madhya Pradesh'
                ORDER BY source_date DESC, mandi
            """
            
            cursor = await db.execute(query, (f"%{crop}%",))
            rows = await cursor.fetchall()
            
            if not rows:
                logger.warning(f"No price history found for {crop}")
                return None
            
            # For each mandi, get its GPS coordinates and calculate distance
            # NOTE: This assumes we have a mandi_locations table OR we geocode on the fly
            # For now, we'll use a simplified approach: filter by district name proximity
            
            results_with_distance = []
            seen_mandis = set()
            
            from app.services.weather_service import weather_service
            
            for row in rows:
                mandi_name = row['mandi']
                
                # Skip duplicates
                if mandi_name in seen_mandis:
                    continue
                    
                seen_mandis.add(mandi_name)
                
                # Try to geocode mandi name
                mandi_location = await weather_service.geocode_location(mandi_name)
                
                if mandi_location:
                    # Calculate distance
                    distance = haversine_distance(
                        user_lat, user_lon,
                        mandi_location['lat'], mandi_location['lon']
                    )
                    
                    if distance <= radius_km:
                        price_data = dict(row)
                        price_data['distance_km'] = distance
                        
                        # Add staleness metadata
                        source_date_str = price_data['source_date']
                        source_date_obj = datetime.strptime(source_date_str, "%Y-%m-%d").date()
                        days_old = (date.today() - source_date_obj).days
                        
                        price_data['is_stale'] = days_old > 0
                        price_data['days_old'] = days_old
                        price_data['date_display'] = source_date_obj.strftime("%d %b")
                        
                        results_with_distance.append(price_data)
            
            if not results_with_distance:
                logger.info(f"No mandis found within {radius_km}km")
                return None
            
            # Sort by distance, return top N
            results_with_distance.sort(key=lambda x: x['distance_km'])
            top_results = results_with_distance[:max_results]
            
            logger.info(f"Found {len(top_results)} mandis within {radius_km}km for {crop}")
            return top_results
            
        except Exception as e:
            logger.error(f"Error in radius search: {e}", exc_info=True)
            return None


# Global service instance
price_query_service = PriceQueryService()
