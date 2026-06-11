import sqlite3
import os

DB_FILE = "krishi_baba.db"

def fix():
    cwd = os.getcwd()
    print(f"📂 CWD: {cwd}")
    db_path = os.path.join(cwd, DB_FILE)
    print(f"🎯 Target DB: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ DB File not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"📋 Tables found: {tables}")
        
        if 'users' not in tables:
            print("❌ 'users' table missing! This is a fresh or broken DB.")
        else:
            # Check columns
            cursor.execute("PRAGMA table_info(users)")
            cols = [c[1] for c in cursor.fetchall()]
            print(f"🔍 Columns in 'users': {cols}")
            
            updates = []
            if 'location_data' not in cols: updates.append("ALTER TABLE users ADD COLUMN location_data JSON")
            if 'crop_summary' not in cols: updates.append("ALTER TABLE users ADD COLUMN crop_summary TEXT")
            
            if updates:
                print(f"🛠️ Applying {len(updates)} fixes...")
                for sql in updates:
                    try:
                        cursor.execute(sql)
                        print(f"   ✅ Executed: {sql}")
                    except Exception as e:
                        print(f"   ❌ Failed: {sql} -> {e}")
                conn.commit()
                print("✨ Verification: Fixes applied.")
            else:
                print("✅ Schema is already correct.")

        conn.close()

    except Exception as e:
        print(f"🔥 Error: {e}")

if __name__ == "__main__":
    fix()
