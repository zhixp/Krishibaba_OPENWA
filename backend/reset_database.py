"""
🧹 ZOMBIE DATA PURGE - Database Reset Script

This script deletes the old database and lets the app recreate it
with the new schema (step, lat, long columns).

CRITICAL: Run this BEFORE testing the new onboarding!
"""
import os
import sys

# Database paths
DB_PATHS = [
    "krishi_baba.db",
    "farmers.db", 
    "sarpanch.db",
    "./krishi_baba.db",
    "./farmers.db",
    "./sarpanch.db"
]

def purge_zombie_data():
    """Delete old database files"""
    print("=" * 70)
    print("🧹 ZOMBIE DATA PURGE - Database Reset")
    print("=" * 70)
    print("\nSearching for database files...")
    
    found = False
    for db_path in DB_PATHS:
        if os.path.exists(db_path):
            found = True
            print(f"\n❌ Found old database: {db_path}")
            
            # Ask for confirmation
            confirm = input(f"   Delete {db_path}? (yes/no): ")
            
            if confirm.lower() == 'yes':
                try:
                    os.remove(db_path)
                    print(f"   ✅ Deleted: {db_path}")
                except Exception as e:
                    print(f"   ⚠️  Error deleting: {e}")
            else:
                print(f"   ⏭️  Skipped: {db_path}")
    
    if not found:
        print("\n✅ No old database files found. System is clean!")
    else:
        print("\n" + "=" * 70)
        print("✅ PURGE COMPLETE!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Restart the backend server")
        print("2. Database will be recreated with new schema")
        print("3. Test onboarding from fresh state")
        print("\nCommand to restart:")
        print("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
    print("\n")

if __name__ == "__main__":
    purge_zombie_data()
