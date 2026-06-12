"""
Pydantic Models for API Request/Response
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime


class UserCreate(BaseModel):
    """Model for creating a new user"""
    uid: str = Field(..., description="Google User ID")
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    default_pincode: Optional[str] = Field(None, pattern=r'^\d{6}$', description="6-digit pincode")
    default_district: Optional[str] = None
    gps_lat: Optional[float] = Field(None, ge=-90, le=90)
    gps_lon: Optional[float] = Field(None, ge=-180, le=180)
    village: Optional[str] = None
    state: Optional[str] = None
    location_source: Optional[Literal["gps", "pincode", "village_text"]] = None
    location_confidence: Optional[Literal["high", "medium", "low"]] = None


class UserProfile(BaseModel):
    """User profile response"""
    uid: str
    name: str
    phone: Optional[str]
    default_pincode: Optional[str]
    default_district: Optional[str]
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    village: Optional[str] = None
    state: Optional[str] = None
    location_source: Optional[str] = None
    location_confidence: Optional[str] = None
    created_at: Optional[datetime]


class ChatRequest(BaseModel):
    """Chat interaction request (text-only for Phase 1)"""
    uid: str = Field(..., description="User ID")
    text_input: str = Field(default="", max_length=1000)
    # GPS coordinates from channel clients when available
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    # Explicit pincode input (Optional - if user types manually)
    pincode_input: Optional[str] = Field(None, pattern=r'^\d{6}$', description="6-digit pincode")
    # Backward compatibility
    location: Optional[dict] = None


class ChatResponse(BaseModel):
    """Chat interaction response"""
    reply_text_hindi: str = Field(..., description="Bot response in Hindi/Hinglish")
    detected_location: Optional[str] = Field(None, description="Extracted location")
    card_type: Optional[str] = Field(None, description="Type of smart card: mandi, weather, scheme, none")
    card_data: Optional[Dict[str, Any]] = Field(None, description="Data for smart card rendering")
    intent: Optional[str] = Field(None, description="Classified intent")


class MandiPrice(BaseModel):
    """Mandi price data"""
    crop_name: str
    mandi_location: str
    modal_price: float
    min_price: Optional[float]
    max_price: Optional[float]
    date_scraped: str
    state: Optional[str]
    district: Optional[str]


class GovtScheme(BaseModel):
    """Government scheme data"""
    scheme_name: str
    benefit_summary: str
    eligibility: Optional[str]
    source_url: Optional[str]
    category: Optional[str]
    state: Optional[str]


class SyncRequest(BaseModel):
    """Request for offline data sync"""
    pincode: str = Field(..., pattern=r'^\d{6}$')
    last_sync_timestamp: Optional[str] = None


class SyncResponse(BaseModel):
    """Response with offline data"""
    mandi_updates: List[MandiPrice] = []
    new_schemes: List[GovtScheme] = []
    sync_timestamp: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    version: str
