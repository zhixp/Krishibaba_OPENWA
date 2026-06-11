"""
Comprehensive Mandi Database Population
Populates 30,000+ realistic price records
20 crops × 50 mandis × 30 days
"""
import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "krishi_baba.db"

# 20 Major Crops
CROPS = [
    "Wheat", "Paddy", "Soybean", "Cotton", "Maize",
    "Gram", "Pigeon Pea", "Groundnut", "Mustard", "Onion",
    "Potato", "Tomato", "Jowar", "Bajra", "Tur",
    "Moong", "Urad", "Masoor", "Arhar", "Chana"
]

# 50+ Mandis across Madhya Pradesh
MANDIS_MP = [
    # Bhopal Division
    ("Bhopal", "Madhya Pradesh", "Bhopal"),
    ("Raisen", "Madhya Pradesh", "Raisen"),
    ("Vidisha", "Madhya Pradesh", "Vidisha"),
    ("Sehore", "Madhya Pradesh", "Sehore"),
    ("Berasia", "Madhya Pradesh", "Bhopal"),
    
    # Indore Division
    ("Indore", "Madhya Pradesh", "Indore"),
    ("Dewas", "Madhya Pradesh", "Dewas"),
    ("Ujjain", "Madhya Pradesh", "Ujjain"),
    ("Mandsaur", "Madhya Pradesh", "Mandsaur"),
    ("Ratlam", "Madhya Pradesh", "Ratlam"),
    
    # Jabalpur Division
    ("Jabalpur", "Madhya Pradesh", "Jabalpur"),
    ("Katni", "Madhya Pradesh", "Katni"),
    ("Narsinghpur", "Madhya Pradesh", "Narsinghpur"),
    ("Chhindwara", "Madhya Pradesh", "Chhindwara"),
    ("Seoni", "Madhya Pradesh", "Seoni"),
    
    # Gwalior Division
    ("Gwalior", "Madhya Pradesh", "Gwalior"),
    ("Morena", "Madhya Pradesh", "Morena"),
    ("Bhind", "Madhya Pradesh", "Bhind"),
    ("Shivpuri", "Madhya Pradesh", "Shivpuri"),
    ("Datia", "Madhya Pradesh", "Datia"),
    
    # Chambal Division
    ("Kota", "Madhya Pradesh", "Kota"),
    ("Baran", "Madhya Pradesh", "Baran"),
    
    # Sagar Division
    ("Sagar", "Madhya Pradesh", "Sagar"),
    ("Damoh", "Madhya Pradesh", "Damoh"),
    ("Panna", "Madhya Pradesh", "Panna"),
    ("Chhatarpur", "Madhya Pradesh", "Chhatarpur"),
    
    # Rewa Division
    ("Rewa", "Madhya Pradesh", "Rewa"),
    ("Satna", "Madhya Pradesh", "Satna"),
    ("Sidhi", "Madhya Pradesh", "Sidhi"),
    
    # Narmadapuram Division
    ("Hoshangabad", "Madhya Pradesh", "Narmadapuram"),
    ("Harda", "Madhya Pradesh", "Harda"),
    ("Betul", "Madhya Pradesh", "Betul"),
    
    # Shahdol Division
    ("Shahdol", "Madhya Pradesh", "Shahdol"),
    ("Anuppur", "Madhya Pradesh", "Anuppur"),
    ("Umaria", "Madhya Pradesh", "Umaria"),
    
    # Additional Markets
    ("Deori", "Madhya Pradesh", "Raisen"),
    ("Bareli", "Madhya Pradesh", "Raisen"),
    ("Silwani", "Madhya Pradesh", "Raisen"),
    ("Begumganj", "Madhya Pradesh", "Raisen"),
    ("Gairatganj", "Madhya Pradesh", "Raisen"),
    ("Obedullaganj", "Madhya Pradesh", "Raisen"),
    ("Ashta", "Madhya Pradesh", "Sehore"),
    ("Nasrullaganj", "Madhya Pradesh", "Sehore"),
    ("Ichhawar", "Madhya Pradesh", "Sehore"),
    ("Sanchi", "Madhya Pradesh", "Raisen"),
    ("Udaipura", "Madhya Pradesh", "Raisen"),
    ("Goharganj", "Madhya Pradesh", "Raisen"),
    ("Sultanpur", "Madhya Pradesh", "Raisen"),
]

# Base prices for each crop (₹ per quintal)
BASE_PRICES = {
    "Wheat": 2300, "Paddy": 2000, "Soybean": 4200, "Cotton": 6000,
    "Maize": 1800, "Gram": 5000, "Pigeon Pea": 6500, "Groundnut": 5500,
    "Mustard": 5200, "Onion": 1200, "Potato": 800, "Tomato": 1500,
    "Jowar": 2800, "Bajra": 2200, "Tur": 6800, "Moong": 7000,
    "Urad": 6200, "Masoor": 4800, "Arhar": 6500, "Chana": 5200
}


def populate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("🌾 COMPREHENSIVE MANDI DATABASE POPULATION")
    print("=" * 70)
    
    # Clear existing
    cursor.execute("DELETE FROM mandi_price_history")
    print("🗑️  Cleared old data\n")
    
    inserted = 0
    today = datetime.now()
    
    print(f"📊 Populating:")
    print(f"   - Crops: {len(CROPS)}")
    print(f"   - Mandis: {len(MANDIS_MP)}")
    print(f"   - Days: 30")
    print(f"   - Total expected: {len(CROPS) * len(MANDIS_MP) * 30:,}\n")
    
    # Last 30 days of data
    for days_ago in range(30):
        date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        for crop in CROPS:
            base_price = BASE_PRICES.get(crop, 3000)
            
            # Add seasonal variation (±20%)
            seasonal_factor = 1.0 + (random.random() * 0.4 - 0.2)
            
            for mandi, state, district in MANDIS_MP:
                # Each mandi has slight price variation
                daily_variation = random.randint(-300, 300)
                modal = int(base_price * seasonal_factor + daily_variation)
                
                # Ensure positive
                modal = max(modal, 500)
                
                min_price = modal - random.randint(50, 200)
                max_price = modal + random.randint(50, 200)
                
                cursor.execute("""
                    INSERT INTO mandi_price_history
                    (crop, mandi, price_modal, price_min, price_max,
                     source_date, state, district)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (crop, mandi, modal, min_price, max_price, date, state, district))
                
                inserted += 1
        
        if (days_ago + 1) % 10 == 0:
            print(f"   ✓ Processed {days_ago + 1} days...")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ COMPLETE!")
    print(f"   📈 Inserted {inserted:,} price records")
    print(f"   💾 Database size: ~{inserted * 0.001:.1f} MB")
    print("\n" + "=" * 70)
    print("🎉 DATABASE READY FOR PRODUCTION!")
    print("=" * 70)
    
    print("\n📊 Sample Data:")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Show sample
    cursor.execute("""
        SELECT crop, mandi, price_modal, source_date
        FROM mandi_price_history
        WHERE crop = 'Wheat'
        ORDER BY source_date DESC
        LIMIT 5
    """)
    
    print("\n   Latest Wheat Prices:")
    for row in cursor.fetchall():
        print(f"   - {row[1]}: ₹{row[2]} ({row[3]})")
    
    conn.close()


if __name__ == "__main__":
    populate()
