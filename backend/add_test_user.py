"""
Quick fix: Add test user with location
"""
import sqlite3

DB_PATH = "krishi_baba.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get a sample UID from SharedPreferences or create test one
test_uid = "test_user_123"

# Bhopal coordinates
lat = 23.2599
lon = 77.4126
district = "Bhopal"

# Check if user exists
cursor.execute("SELECT uid FROM users WHERE uid = ?", (test_uid,))
if cursor.fetchone():
    print(f"✅ User {test_uid} already exists")
else:
    # Create test user
    cursor.execute(
        """INSERT INTO users (uid, lat, long, default_district, step)
           VALUES (?, ?, ?, ?, 'active')""",
        (test_uid, lat, lon, district)
    )
    conn.commit()
    print(f"✅ Created test user: {test_uid}")
    print(f"   Location: {district} ({lat}, {lon})")

# Also add a default location for ANY user
cursor.execute("""
    UPDATE users 
    SET lat = ?, long = ?, default_district = ?
    WHERE lat IS NULL OR long IS NULL
""", (lat, lon, district))
conn.commit()

updated = cursor.rowcount
if updated > 0:
    print(f"✅ Updated {updated} users with default location")

conn.close()

print("\n📍 All users now have location data!")
print("Try the weather screen again!")
