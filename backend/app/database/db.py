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
                gps_lat REAL,
                gps_lon REAL,
                village TEXT,
                state TEXT,
                location_source TEXT,
                location_confidence TEXT,
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

        user_location_columns = {
            "gps_lat": "ALTER TABLE users ADD COLUMN gps_lat REAL",
            "gps_lon": "ALTER TABLE users ADD COLUMN gps_lon REAL",
            "village": "ALTER TABLE users ADD COLUMN village TEXT",
            "state": "ALTER TABLE users ADD COLUMN state TEXT",
            "location_source": "ALTER TABLE users ADD COLUMN location_source TEXT",
            "location_confidence": "ALTER TABLE users ADD COLUMN location_confidence TEXT",
        }
        for column_name, alter_sql in user_location_columns.items():
            if column_name not in existing_columns:
                await db.execute(alter_sql)

        await db.execute("""
            UPDATE users
            SET gps_lat = lat,
                gps_lon = long,
                location_source = COALESCE(location_source, 'gps'),
                location_confidence = COALESCE(location_confidence, 'high')
            WHERE lat IS NOT NULL
              AND long IS NOT NULL
              AND gps_lat IS NULL
              AND gps_lon IS NULL
              AND (location_source IS NULL OR location_source = '')
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_location_source
            ON users(location_source, location_confidence)
        """)
        
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
                consent_granted INTEGER DEFAULT 0,
                dialect_guess TEXT,
                location_hint TEXT,
                crop_hint TEXT,
                intent TEXT,
                confidence REAL,
                response TEXT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(uid)
            )
        """)

        # MIGRATION: Add structured voice metadata fields to existing installs.
        cursor = await db.execute("PRAGMA table_info(voice_logs)")
        columns = await cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        voice_columns = {
            "consent_granted": "ALTER TABLE voice_logs ADD COLUMN consent_granted INTEGER DEFAULT 0",
            "dialect_guess": "ALTER TABLE voice_logs ADD COLUMN dialect_guess TEXT",
            "location_hint": "ALTER TABLE voice_logs ADD COLUMN location_hint TEXT",
            "crop_hint": "ALTER TABLE voice_logs ADD COLUMN crop_hint TEXT",
            "intent": "ALTER TABLE voice_logs ADD COLUMN intent TEXT",
            "confidence": "ALTER TABLE voice_logs ADD COLUMN confidence REAL",
            "response": "ALTER TABLE voice_logs ADD COLUMN response TEXT",
            "feedback": "ALTER TABLE voice_logs ADD COLUMN feedback TEXT",
        }
        for column_name, alter_sql in voice_columns.items():
            if column_name not in existing_columns:
                await db.execute(alter_sql)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_voice_logs_user_created
            ON voice_logs(user_id, created_at DESC)
        """)

        # Uploaded images table (future disease detection)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                filename TEXT NOT NULL,
                crop_type TEXT,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uid) REFERENCES users(uid)
            )
        """)

        cursor = await db.execute("PRAGMA table_info(uploaded_images)")
        columns = await cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        if "file_size" not in existing_columns:
            await db.execute("ALTER TABLE uploaded_images ADD COLUMN file_size INTEGER")

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_uploaded_images_uid_created
            ON uploaded_images(uid, created_at DESC)
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
