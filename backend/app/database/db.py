"""
Database Schema and Initialization
SQLite database with async support (aiosqlite)
"""
import aiosqlite
from pathlib import Path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Extract database path from URL
DB_PATH = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")


async def init_db():
    """Initialize database and create tables if they don't exist"""
    db_file = Path(DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Enable foreign keys
        await db.execute("PRAGMA foreign_keys = ON")
        
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid TEXT PRIMARY KEY,
                name TEXT,
                phone TEXT,
                default_pincode TEXT,
                default_district TEXT,
                lat REAL,
                long REAL,
                location_data JSON,
                crops TEXT,
                crop_summary TEXT,  -- The Notebook
                step TEXT DEFAULT 'name',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # MIGRATION: Add missing columns to existing users table
        # (CREATE TABLE IF NOT EXISTS doesn't update existing schemas)
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        if 'location_data' not in existing_columns:
            logger.info("🔧 Adding missing 'location_data' column to users table...")
            await db.execute("ALTER TABLE users ADD COLUMN location_data JSON")
            
        if 'crop_summary' not in existing_columns:
            logger.info("🔧 Adding missing 'crop_summary' column to users table...")
            await db.execute("ALTER TABLE users ADD COLUMN crop_summary TEXT")
        
        # Chat messages table for conversation memory
        await db.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uid) REFERENCES users(uid)
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
        
        # Mandi price HISTORY table (for price movement tracking)
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
        
        # Create indexes for price history (for fast queries)
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
        
        # BULLETPROOF INDEX: Fast crop+location+date queries
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_crop_state_date
            ON mandi_price_history(crop, state, source_date DESC)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_crop_district_date
            ON mandi_price_history(crop, district, source_date DESC)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mandi_history_crop_date 
            ON mandi_price_history(crop, source_date DESC)
        """)
        
        # Ad Campaigns table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ad_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                keywords TEXT NOT NULL,
                cta TEXT NOT NULL,
                cta_link TEXT,
                icon TEXT DEFAULT '📢',
                relevance_threshold REAL DEFAULT 0.5,
                location_filter TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ad Impressions table (for cooldown tracking)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ad_impressions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                campaign_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES ad_campaigns(id)
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_impressions_uid_campaign
            ON ad_impressions(uid, campaign_id, created_at DESC)
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
        
        # Chat history table (for analytics/debugging)
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
        
        # Voice logs table (for Voice Vault - dataset collection)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS voice_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                transcription TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(uid)
            )
        """)
        
        # User facts table (for AI training - extracted knowledge)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                fact_type TEXT NOT NULL,
                fact_value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(uid)
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_facts_type
            ON user_facts(user_id, fact_type)
        """)
        
        await db.commit()
        logger.info("✅ Database tables created/verified successfully")



async def get_db():
    """Dependency for getting database connection"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row  # Return rows as dictionaries
        yield db
