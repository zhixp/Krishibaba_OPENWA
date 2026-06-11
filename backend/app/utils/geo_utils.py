"""
Geo-Distance Calculator - Haversine Formula
Used for finding mandis within radius of user's GPS location
"""
import math
from typing import Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates in kilometers
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
        
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 2)


def is_within_radius(
    user_lat: float, 
    user_lon: float, 
    target_lat: float, 
    target_lon: float, 
    radius_km: float = 100
) -> bool:
    """
    Check if target coordinates are within radius of user's location
    
    Args:
        user_lat, user_lon: User's GPS location
        target_lat, target_lon: Target location (e.g., mandi)
        radius_km: Radius in kilometers (default: 100km)
        
    Returns:
        True if within radius, False otherwise
    """
    distance = haversine_distance(user_lat, user_lon, target_lat, target_lon)
    return distance <= radius_km
