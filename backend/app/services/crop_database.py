"""
Crop Database - Maps Hindi/English crop names to agriplus.in slugs
Migrated from old WhatsApp implementation
"""

# Comprehensive crop mapping for Indian markets
CROP_DATABASE = {
    # Grains/Cereals
    "गेहूं": "wheat",
    "Wheat": "wheat",
    "Gehun": "wheat",
    "धान": "paddy-dhan",
    "Paddy": "paddy-dhan",
    "Dhan": "paddy-dhan",
    "Rice": "paddy-dhan",
    "मक्का": "maize",
    "Maize": "maize",
    "Makka": "maize",
    "Corn": "maize",
    "बाजरा": "bajra-pearl-millet",
    "Bajra": "bajra-pearl-millet",
    "Pearl Millet": "bajra-pearl-millet",
    "ज्वार": "jowar",
    "Jowar": "jowar",
    "Sorghum": "jowar",
    
    # Pulses
    "सोयाबीन": "soybean",
    "Soybean": "soybean",
    "Soya": "soybean",
    "चना": "gram",
    "Gram": "gram",
    "Chana": "gram",
    "Chickpea": "gram",
    "अरहर": "arhar-tur-red-gram",
    "Arhar": "arhar-tur-red-gram",
    "Tur": "arhar-tur-red-gram",
    "Pigeon Pea": "arhar-tur-red-gram",
    "मूंग": "green-gram-moong",
    "Moong": "green-gram-moong",
    "Green Gram": "green-gram-moong",
    "उड़द": "black-gram-urd-beans",
    "Urad": "black-gram-urd-beans",
    "Black Gram": "black-gram-urd-beans",
    "मसूर": "lentil-masur",
    "Masur": "lentil-masur",
    "Lentil": "lentil-masur",
    
    # Oilseeds
    "मूंगफली": "groundnut",
    "Groundnut": "groundnut",
    "Moongfali": "groundnut",
    "Peanut": "groundnut",
    "सरसों": "mustard",
    "Mustard": "mustard",
    "Sarson": "mustard",
    "तिल": "sesame-sesamum",
    "Sesame": "sesame-sesamum",
    "Til": "sesame-sesamum",
    "सूरजमुखी": "sunflower",
    "Sunflower": "sunflower",
    
    # Cash Crops
    "कपास": "cotton",
    "Cotton": "cotton",
    "Kapas": "cotton",
    "गन्ना": "sugarcane",
    "Sugarcane": "sugarcane",
    "Ganna": "sugarcane",
    
    # Spices
    "हल्दी": "turmeric",
    "Turmeric": "turmeric",
    "Haldi": "turmeric",
    "मिर्च": "chili-red",
    "Chili": "chili-red",
    "Mirch": "chili-red",
    "धनिया": "coriander-seed",
    "Coriander": "coriander-seed",
    "Dhaniya": "coriander-seed",
    "जीरा": "cumin-seed-jeera",
    "Jeera": "cumin-seed-jeera",
    "Cumin": "cumin-seed-jeera",
    
    # Vegetables
    "प्याज": "onion",
    "Onion": "onion",
    "Pyaj": "onion",
    "आलू": "potato",
    "Potato": "potato",
    "Aloo": "potato",
    "टमाटर": "tomato",
    "Tomato": "tomato",
    "Tamatar": "tomato",
}

# State name to slug mapping
STATE_MAP = {
    "madhya pradesh": "madhya-pradesh",
    "mp": "madhya-pradesh",
    "uttar pradesh": "uttar-pradesh",
    "up": "uttar-pradesh",
    "rajasthan": "rajasthan",
    "maharashtra": "maharashtra",
    "punjab": "punjab",
    "haryana": "haryana",
    "bihar": "bihar",
    "west bengal": "west-bengal",
    "gujarat": "gujarat",
    "karnataka": "karnataka",
    "tamil nadu": "tamil-nadu",
    "andhra pradesh": "andhra-pradesh",
    "telangana": "telangana",
}


def normalize_crop_name(crop_name: str) -> str:
    """
    Normalize crop name to agriplus.in slug
    
    Args:
        crop_name: Hindi/English crop name
    
    Returns:
        Slug for agriplus.in URL, or None if not found
    """
    # Try exact match first
    if crop_name in CROP_DATABASE:
        return CROP_DATABASE[crop_name]
    
    # Try case-insensitive match
    for key, value in CROP_DATABASE.items():
        if key.lower() == crop_name.lower():
            return value
    
    return None


def normalize_state_name(state_name: str) -> str:
    """
    Normalize state name to agriplus.in slug
    
    Args:
        state_name: State name
    
    Returns:
        Slug for agriplus.in URL, or None if not found
    """
    state_lower = state_name.lower().strip()
    return STATE_MAP.get(state_lower)


def get_available_crops() -> list:
    """Get list of all available crops"""
    unique_crops = set()
    for crop_name in CROP_DATABASE.keys():
        # Only return English names
        if crop_name[0].isupper():
            unique_crops.add(crop_name)
    return sorted(list(unique_crops))


def get_available_states() -> list:
    """Get list of all available states"""
    return sorted([k.title() for k in STATE_MAP.keys() if len(k) > 2])  # Exclude abbreviations
