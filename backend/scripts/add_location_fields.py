"""
Initialize Database and Run Migration
This script initializes the database with all tables, then adds the new columns.
"""
import aiosqlite
import asyncio
from pathlib import Path

DB_PATH = "./krishi_baba.db"


async def init_db():
    """Initialize database and create tables if they don't exist"""
    print("🔧 Initializing database...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Enable foreign keys
        await db.execute("PRAGMA foreign_keys = ON")
        
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                default_pincode TEXT NOT NULL,
                default_district TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Mandi prices table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mandi_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop_name TEXT NOT NULL,
                mandi_location TEXT NOT NULL,
                modal_price REAL NOT NULL,
                min_price REAL,
                max_price REAL,
                date_scraped TEXT NOT NULL,
                state TEXT,
                district TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for mandi prices
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mandi_crop 
            ON mandi_prices(crop_name)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mandi_location 
            ON mandi_prices(mandi_location)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mandi_date 
            ON mandi_prices(date_scraped)
        """)
        
        # Mandi price HISTORY table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mandi_price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop TEXT NOT NULL,
                mandi TEXT NOT NULL,
                price_min REAL,
                price_max REAL,
                price_modal REAL NOT NULL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_date DATE NOT NULL,
                state TEXT,
                district TEXT,
                traded_quantity TEXT,
                arrivals_quantity TEXT,
                arrival_tonnes REAL DEFAULT 0,
                UNIQUE(crop, mandi, source_date)
            )
        """)
        
        # Create indexes for price history
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_crop 
            ON mandi_price_history(crop)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_mandi 
            ON mandi_price_history(mandi)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_date 
            ON mandi_price_history(source_date DESC)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_lookup 
            ON mandi_price_history(crop, mandi, source_date DESC)
        """)
        
        # Government schemes table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS govt_schemes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheme_name TEXT NOT NULL,
                benefit_summary TEXT NOT NULL,
                eligibility TEXT,
                source_url TEXT,
                category TEXT,
                state TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Chat history table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_message TEXT,
                bot_response TEXT,
                intent TEXT,
                detected_location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(uid)
            )
        """)
        
        await db.commit()
        print("✅ Database tables created successfully")


async def check_column_exists(db: aiosqlite.Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table"""
    cursor = await db.execute(f"PRAGMA table_info({table})")
    columns = await cursor.fetchall()
    column_names = [col[1] for col in columns]
    return column in column_names


async def add_new_columns():
    """Add new columns to users table"""
    print("\n🔧 Adding new columns to users table...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        migrations_run = []
        
        # 1. Add latitude column
        if not await check_column_exists(db, "users", "lat"):
            print("➕ Adding 'lat' column...")
            await db.execute("ALTER TABLE users ADD COLUMN lat REAL")
            migrations_run.append("lat")
        else:
            print("✓ Column 'lat' already exists")
        
        # 2. Add longitude column
        if not await check_column_exists(db, "users", "long"):
            print("➕ Adding 'long' column...")
            await db.execute("ALTER TABLE users ADD COLUMN long REAL")
            migrations_run.append("long")
        else:
            print("✓ Column 'long' already exists")
        
        # 3. Add crops column
        if not await check_column_exists(db, "users", "crops"):
            print("➕ Adding 'crops' column...")
            await db.execute("ALTER TABLE users ADD COLUMN crops TEXT")
            migrations_run.append("crops")
        else:
            print("✓ Column 'crops' already exists")
        
        # 4. Add last_active column
        if not await check_column_exists(db, "users", "last_active"):
            print("➕ Adding 'last_active' column...")
            await db.execute(
                "ALTER TABLE users ADD COLUMN last_active DATETIME DEFAULT CURRENT_TIMESTAMP"
            )
            migrations_run.append("last_active")
        else:
            print("✓ Column 'last_active' already exists")
        
        # Commit all changes
        if migrations_run:
            await db.commit()
            print(f"\n✅ Added columns: {', '.join(migrations_run)}")
        else:
            print("\n✅ All columns already exist")
        
        # Show updated schema
        print("\n📋 Updated users table schema:")
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            nullable = "NOT NULL" if not_null else "NULLABLE"
            pk_indicator = " [PRIMARY KEY]" if pk else ""
            print(f"  - {name} ({col_type}) {nullable}{pk_indicator}")


async def main():
    """Run full migration"""
    print("=" * 60)
    print("  Sarpanch AI - Database Setup & Migration")
    print("=" * 60)
    print()
    
    # Step 1: Initialize database
    await init_db()
    
    # Step 2: Add new columns
    await add_new_columns()
    
    print("\n" + "=" * 60)
    print("  Setup Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
