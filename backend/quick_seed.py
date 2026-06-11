"""
Quick Mandi Data Populator
Adds test data to mandi_price_history table
"""
import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "krishi_baba.db"

def populate_mandi_data():
    print("=" * 60)
    print("🚜 Populating Mandi Price Data")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crops (matching what users will ask for)
    crops = [
        "Wheat", "Paddy", "Soybean", "Cotton", "Maize", 
        "Gram", "Pigeon Pea", "Groundnut", "Mustard"
    ]
    
    # Mandis in Madhya Pradesh
    mandis = [
        ("Bhopal", "Madhya Pradesh", "Bhopal"),
        ("Raisen", "Madhya Pradesh", "Raisen"),
        ("Deori", "Madhya Pradesh", "Raisen"),
        ("Vidisha", "Madhya Pradesh", "Vidisha"),
        ("Udaipura", "Madhya Pradesh", "Raisen"),
        ("Indore", "Madhya Pradesh", "Indore"),
    ]
    
    # Clear existing data
    cursor.execute("DELETE FROM mandi_price_history")
    
    inserted = 0
    today = datetime.now()
    
    # Add data for last 3 days
    for days_ago in range(3):
        date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        for crop in crops:
            for mandi, state, district in mandis:
                # Generate realistic prices
                base = random.randint(2500, 5500)
                modal = base
                min_p = base - random.randint(100, 300)
                max_p = base + random.randint(100, 300)
                
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
    print(f"   Crops: {len(crops)}")
    print(f"   Mandis: {len(mandis)}")
    print(f"   Days: 3")
    print("\n" + "=" * 60)
    print("✅ Database Ready!")
    print("=" * 60)
    print("\nTest queries:")
    print("  - 'wheat ka bhav'")
    print("  - 'dhan ka rate'")
    print("  - 'soybean price'")
    print()

if __name__ == "__main__":
    populate_mandi_data()
