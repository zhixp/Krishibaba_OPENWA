"""
Add last_active column if missing
"""
import asyncio
import aiosqlite

DB_PATH = "backend/krishi_baba.db"

async def check_and_add_column():
    """Check if last_active exists and add if missing"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check current schema
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("Current columns:", column_names)
        
        if "crop_summary" not in column_names:
            print("\n➕ Adding crop_summary column...")
            await db.execute(
                "ALTER TABLE users ADD COLUMN crop_summary TEXT"
            )
            await db.commit()
            print("✅ crop_summary added!")

        if "location_data" not in column_names:
            print("\n➕ Adding location_data column...")
            await db.execute(
                "ALTER TABLE users ADD COLUMN location_data JSON"
            )
            await db.commit()
            print("✅ location_data added!")
        
        # Update existing users
        await db.execute(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE last_active IS NULL"
        )
        await db.commit()
        
        print("✅ Database schema updated!")

if __name__ == "__main__":
    asyncio.run(check_and_add_column())
