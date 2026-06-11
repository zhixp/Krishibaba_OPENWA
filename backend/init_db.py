"""
Initialize Database and Create All Tables
Run this FIRST before populating data
"""
import asyncio
import aiosqlite
import sys

DB_PATH = "krishi_baba.db"

async def init_database():
    print("=" * 60)
    print("🗄️  INITIALIZING DATABASE")
    print("=" * 60)
    
    conn = await aiosqlite.connect(DB_PATH)
    
    # Create mandi_price_history table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS mandi_price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop TEXT NOT NULL,
            mandi TEXT NOT NULL,
            price_modal REAL,
            price_min REAL,
            price_max REAL,
            source_date TEXT,
            state TEXT,
            district TEXT,
            variety TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create users table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            crops TEXT,
            lat REAL,
            long REAL,
            default_district TEXT,
            location_data TEXT,
            step TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create chat_history table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uid) REFERENCES users(uid)
        )
    """)
    
    # Create uploaded_images table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            filename TEXT NOT NULL,
            crop_type TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uid) REFERENCES users(uid)
        )
    """)
    
    # Create indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crop_state_date 
        ON mandi_price_history(crop, state, source_date DESC)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crop_district_date 
        ON mandi_price_history(crop, district, source_date DESC)
    """)
    
    await conn.commit()
    
    # Verify tables
    cursor = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = await cursor.fetchall()
    
    print("\n✅ Tables Created:")
    for table in tables:
        print(f"   - {table[0]}")
    
    await conn.close()
    
    print("\n" + "=" * 60)
    print("✅ DATABASE READY!")
    print("=" * 60)
    print("\nNow run: python populate_mandi.py")

if __name__ == "__main__":
    asyncio.run(init_database())
