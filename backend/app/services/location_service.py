"""
GPS-first location resolution for onboarding and weather.
"""
from typing import Any, Dict, Optional

from app.services.weather_service import weather_service


LOCATION_ONBOARDING_MESSAGE = (
    "📍 सही मौसम बताने के लिए आपकी लोकेशन चाहिए।\n\n"
    "नीचे 📎 / + पर दबाओ → Location चुनो → Current Location भेज दो।\n\n"
    "अगर लोकेशन नहीं भेज पा रहे हो, तो 6 अंकों का पिनकोड भेज दो।"
)


def weather_location_note(source: str) -> str:
    if source == "gps":
        return "📍 मौसम रिपोर्ट: आपकी भेजी हुई लोकेशन के आधार पर"
    if source == "pincode":
        return (
            "📍 मौसम रिपोर्ट: आपके पिनकोड क्षेत्र के आधार पर\n"
            "नोट: यह अनुमानित लोकेशन है। ज्यादा सटीक मौसम के लिए WhatsApp location भेजें।"
        )
    if source == "village_text":
        return (
            "📍 मौसम रिपोर्ट: आपके बताए गांव/जिले के आधार पर\n"
            "अगर मौसम बहुत जरूरी है, तो Current Location भेज दें।"
        )
    return LOCATION_ONBOARDING_MESSAGE


def location_confidence_for_source(source: str) -> str:
    if source == "gps":
        return "high"
    if source == "pincode":
        return "medium"
    if source == "village_text":
        return "low"
    return "low"


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


async def resolve_onboarding_location(
    *,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    pincode: Optional[str] = None,
    village: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Resolve location with strict priority:
    1. GPS
    2. Pincode
    3. Village + district
    4. State alone is rejected for weather
    """
    pincode = _clean_text(pincode)
    village = _clean_text(village)
    district = _clean_text(district)
    state = _clean_text(state)

    if latitude is not None or longitude is not None:
        if latitude is None or longitude is None:
            return {
                "success": False,
                "needs_location": True,
                "message": "Latitude aur longitude dono chahiye. Current Location dobara bhej do.",
            }

        loc_data = await weather_service.reverse_geocode(latitude, longitude) or {}
        return {
            "success": True,
            "lat": latitude,
            "lon": longitude,
            "gps_lat": latitude,
            "gps_lon": longitude,
            "location_source": "gps",
            "location_confidence": "high",
            "pincode": pincode,
            "village": loc_data.get("location_name") or village,
            "district": loc_data.get("district") or district,
            "state": loc_data.get("state") or state,
            "location_name": loc_data.get("location_name") or loc_data.get("district") or "GPS location",
            "location_data": loc_data,
            "message": "✅ लोकेशन सेव हो गई। मौसम अब आपकी भेजी हुई लोकेशन से देखा जाएगा।",
        }

    if pincode:
        if not (pincode.isdigit() and len(pincode) == 6):
            return {
                "success": False,
                "needs_location": True,
                "message": "पिनकोड 6 अंकों का होना चाहिए। Current Location भेज दें तो मौसम ज्यादा सही मिलेगा।",
            }

        loc_data = await weather_service.geocode_location(pincode)
        if not loc_data:
            return {
                "success": False,
                "needs_location": True,
                "message": "यह पिनकोड समझ नहीं आया। Current Location भेज दें या गांव + जिला लिख दें।",
            }

        return {
            "success": True,
            "lat": loc_data["lat"],
            "lon": loc_data["lon"],
            "gps_lat": None,
            "gps_lon": None,
            "location_source": "pincode",
            "location_confidence": "medium",
            "pincode": pincode,
            "village": village,
            "district": loc_data.get("district") or district,
            "state": loc_data.get("state") or state,
            "location_name": loc_data.get("location_name") or loc_data.get("district") or pincode,
            "location_data": loc_data,
            "message": "✅ पिनकोड सेव हो गया। मौसम अनुमानित रहेगा; ज्यादा सटीक मौसम के लिए Current Location भेजें।",
        }

    if village:
        if not district:
            return {
                "success": False,
                "needs_district": True,
                "message": f"भैया, {village} नाम के कई गांव हो सकते हैं। जिला भी लिख दो।",
            }

        query_parts = [village, district]
        if state:
            query_parts.append(state)
        loc_data = await weather_service.geocode_location(", ".join(query_parts))
        if not loc_data:
            return {
                "success": False,
                "needs_location": True,
                "message": "गांव/जिला समझ नहीं आया। Current Location भेज दें या 6 अंकों का पिनकोड लिख दें।",
            }

        return {
            "success": True,
            "lat": loc_data["lat"],
            "lon": loc_data["lon"],
            "gps_lat": None,
            "gps_lon": None,
            "location_source": "village_text",
            "location_confidence": "low",
            "pincode": None,
            "village": village,
            "district": loc_data.get("district") or district,
            "state": loc_data.get("state") or state,
            "location_name": loc_data.get("location_name") or village,
            "location_data": loc_data,
            "message": "✅ गांव/जिला सेव हो गया। मौसम अनुमानित रहेगा; ज्यादा सटीक मौसम के लिए Current Location भेजें।",
        }

    if state:
        return {
            "success": False,
            "needs_location": True,
            "message": "सिर्फ राज्य से मौसम सही नहीं बता सकता। Current Location भेज दें, या पिनकोड / गांव + जिला लिख दें।",
        }

    return {
        "success": False,
        "needs_location": True,
        "message": LOCATION_ONBOARDING_MESSAGE,
    }


def build_weather_location_from_user(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Pick the safest saved location for weather. GPS always wins."""
    gps_lat = user.get("gps_lat")
    gps_lon = user.get("gps_lon")
    lat = user.get("lat")
    lon = user.get("long")
    source = user.get("location_source")

    if gps_lat is not None and gps_lon is not None:
        return {
            "lat": gps_lat,
            "lon": gps_lon,
            "source": "gps",
            "confidence": "high",
            "display_name": user.get("village") or user.get("default_district") or "आपकी लोकेशन",
        }

    if lat is not None and lon is not None and source in {"pincode", "village_text", "gps"}:
        safe_source = source or "pincode"
        return {
            "lat": lat,
            "lon": lon,
            "source": safe_source,
            "confidence": user.get("location_confidence") or location_confidence_for_source(safe_source),
            "display_name": user.get("village") or user.get("default_district") or user.get("default_pincode") or "आपका क्षेत्र",
        }

    return None
