"""
Fix: Ensure users have location OR allow weather without user
"""
import sqlite3
from datetime import datetime

DB_PATH = "krishi_baba.db"

def fix_user_system():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🔧 FIXING USER SYSTEM")
    print("=" * 60)
    
    # Create a test user with location
    test_uid = "test_user_123"
    
    cursor.execute("""
        INSERT OR REPLACE INTO users
        (uid, name, lat, long, default_district, step, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (test_uid, "Test किसान", 23.2599, 77.4126, "Bhopal", "active", datetime.now()))
    
    conn.commit()
    
    print(f"✅ Created test user: {test_uid}")
    print(f"   Name: Test किसान")
    print(f"   Location: Bhopal (23.2599, 77.4126)")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"\n📊 Total users: {count}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ FIXED! Now test the app")
    print("=" * 60)
    print("\nUID to use in local channel tests: test_user_123")
    print("Or send a WhatsApp/channel message - it will create or update the farmer")

if __name__ == "__main__":
    fix_user_system()
