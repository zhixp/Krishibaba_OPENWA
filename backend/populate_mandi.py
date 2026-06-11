"""
Populate Mandi Database with Real Sample Data
Run this to fill mandi_price_history table
"""
import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "krishi_baba.db"

# Real crops and mandis
CROPS = [
    "Wheat", "Paddy", "Soybean", "Cotton", "Maize",
    "Gram", "Pigeon Pea", "Groundnut", "Mustard", "Onion"
]

MANDIS_MP = [
    ("Bhopal", "Madhya Pradesh", "Bhopal"),
    ("Indore", "Madhya Pradesh", "Indore"),
    ("Raisen", "Madhya Pradesh", "Raisen"),
    ("Deori", "Madhya Pradesh", "Raisen"),
    ("Vidisha", "Madhya Pradesh", "Vidisha"),
    ("Sehore", "Madhya Pradesh", "Sehore"),
    ("Gwalior", "Madhya Pradesh", "Gwalior"),
    ("Jabalpur", "Madhya Pradesh", "Jabalpur"),
    ("Ujjain", "Madhya Pradesh", "Ujjain"),
    ("Dewas", "Madhya Pradesh", "Dewas"),
]

def populate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🌾 Populating Mandi Database")
    print("=" * 60)
    
    # Clear existing
    cursor.execute("DELETE FROM mandi_price_history")
    print("🗑️  Cleared old data")
    
    inserted = 0
    today = datetime.now()
    
    # Last 7 days of data
    for days_ago in range(7):
        date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        for crop in CROPS:
            # Base price depends on crop
            if crop == "Wheat":
                base = random.randint(2200, 2600)
            elif crop == "Paddy":
                base = random.randint(1800, 2200)
            elif crop == "Soybean":
                base = random.randint(4000, 4800)
            elif crop == "Cotton":
                base = random.randint(5500, 6500)
            elif crop == "Onion":
                base = random.randint(800, 1500)
            else:
                base = random.randint(3000, 5000)
            
            for mandi, state, district in MANDIS_MP:
                # Slight variation per mandi
                modal = base + random.randint(-200, 200)
                min_p = modal - random.randint(50, 150)
                max_p = modal + random.randint(50, 150)
                
                cursor.execute("""
                    INSERT INTO mandi_price_history
                    (crop, mandi, price_modal, price_min, price_max,
                     source_date, state, district, variety)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (crop, mandi, modal, min_p, max_p, date, state, district, "Standard"))
                
                inserted += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Inserted {inserted} price records")
    print(f"   📊 Crops: {len(CROPS)}")
    print(f"   📍 Mandis: {len(MANDIS_MP)}")
    print(f"   📅 Days: 7")
    print("\n" + "=" * 60)
    print("✅ Database Ready!")
    print("=" * 60)
    print("\nNow test Mandi screen:")
    print("  - Search 'wheat'")
    print("  - Should show prices from all mandis!")

if __name__ == "__main__":
    populate()
