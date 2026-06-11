"""
List all existing users in database
"""
import asyncio
import aiosqlite

DB_PATH = "./krishi_baba.db"

async def list_users():
    """Show all existing users"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT uid, name, default_pincode, default_district, lat, long, crops FROM users LIMIT 20")
        users = await cursor.fetchall()
        
        if not users:
            print("❌ No users found in database")
            return
        
        print(f"📋 Found {len(users)} existing test users:")
        print("=" * 80)
        
        for user in users:
            print(f"\n✅ UID: {user[0]}")
            print(f"   Name: {user[1]}")
            print(f"   Pincode: {user[2]}")
            print(f"   Location: {user[3]}")
            print(f"   Lat/Long: {user[4]}, {user[5]}")
            print(f"   Crops: {user[6]}")
        
        print("\n" + "=" * 80)
        print(f"\n🧪 Use any of these UIDs for testing:")
        print(f'   Example: {{"uid":"{users[0][0]}","text_input":"Hello"}}')

if __name__ == "__main__":
    asyncio.run(list_users())
