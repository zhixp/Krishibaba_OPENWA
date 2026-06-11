import sqlite3
import os

# Use the relative path as it will be run from backend dir
DB_FILE = "krishi_baba.db"

def nuke_users_table():
    cwd = os.getcwd()
    print(f"📂 CWD: {cwd}")
    db_path = os.path.abspath(DB_FILE)
    print(f"🎯 Target DB: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ DB File not found at {db_path}. Nothing to drop.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("💣 Dropping 'users' table...")
        try:
            cursor.execute("DROP TABLE IF EXISTS users")
            print("   ✅ Dropped 'users' table.")
        except Exception as e:
            print(f"   ❌ Failed to drop table: {e}")
            
        conn.commit()
        
        # Verify it's gone
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
             print("   ⚠️ Table still exists! (Locked?)")
        else:
             print("   ✨ Table confirmed deleted.")

        conn.close()

    except Exception as e:
        print(f"🔥 Error: {e}")

if __name__ == "__main__":
    nuke_users_table()
