import sqlite3
import os

DB_FILENAME = "krishi_baba.db"
CWD = os.getcwd()
DB_PATH = os.path.join(CWD, DB_FILENAME)

print(f"📂 CWD: {CWD}")
print(f"🎯 Expected DB Path: {DB_PATH}")

if os.path.exists(DB_PATH):
    print(f"✅ File exists. Size: {os.path.getsize(DB_PATH)} bytes")
else:
    print("❌ File DOES NOT exist in CWD.")
    # Try looking in subfolder if we are in root
    alt_path = os.path.join(CWD, "backend", DB_FILENAME)
    if os.path.exists(alt_path):
        print(f"⚠️ Found it in subfolder: {alt_path}")
        DB_PATH = alt_path

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n📋 Listing Tables:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for t in tables:
        print(f" - {t[0]}")
        
    if ('users',) in tables:
        print("\n🔍 Checking 'users' table columns:")
        cursor.execute("PRAGMA table_info(users)")
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        print(f"   Columns: {col_names}")
        
        # FIX IT HERE IF FOUND
        missing = []
        if 'location_data' not in col_names: missing.append('location_data')
        if 'crop_summary' not in col_names: missing.append('crop_summary')
        
        if missing:
            print(f"\n🛠️ Attempting to add missing columns: {missing}")
            for m in missing:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {m} TEXT") # JSON is TEXT
                    print(f"   ✅ Added {m}")
                    conn.commit()
                except Exception as e:
                    print(f"   ❌ Failed to add {m}: {e}")
        else:
             print("\n✅ All columns present.")

    else:
        print("\n❌ Table 'users' NOT FOUND.")

    conn.close()

except Exception as e:
    print(f"🔥 Error: {e}")
