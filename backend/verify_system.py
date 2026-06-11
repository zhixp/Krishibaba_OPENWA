"""
System Verification Script
Tests all critical components
"""
import asyncio
import aiosqlite
import sys

DB_PATH = "krishi_baba.db"


async def verify_system():
    print("=" * 70)
    print("🔍 SYSTEM VERIFICATION")
    print("=" * 70)
    
    checks_passed = 0
    checks_total = 0
    
    try:
        conn = await aiosqlite.connect(DB_PATH)
        
        # CHECK 1: Database exists and has tables
        print("\n✓ Checking database...")
        checks_total += 1
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in await cursor.fetchall()]
        required_tables = ['users', 'chat_messages', 'mandi_price_history']
        
        if all(t in tables for t in required_tables):
            print(f"  ✅ All tables present: {len(tables)} total")
            checks_passed += 1
        else:
            print(f"  ❌ Missing tables! Found: {tables}")
        
        # CHECK 2: Mandi data populated
        print("\n✓ Checking mandi data...")
        checks_total += 1
        cursor = await conn.execute("SELECT COUNT(*) FROM mandi_price_history")
        count = (await cursor.fetchone())[0]
        
        if count >= 1000:
            print(f"  ✅ Mandi database populated: {count:,} records")
            checks_passed += 1
        else:
            print(f"  ⚠️  Mandi data low: only {count} records")
        
        # CHECK 3: Chat memory table ready
        print("\n✓ Checking chat memory...")
        checks_total += 1
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM chat_messages"
        )
        msg_count = (await cursor.fetchone())[0]
        print(f"  ✅ Chat messages table ready ({msg_count} messages)")
        checks_passed += 1
        
        # CHECK 4: Sample crop availability
        print("\n✓ Checking crop variety...")
        checks_total += 1
        cursor = await conn.execute(
            "SELECT DISTINCT crop FROM mandi_price_history"
        )
        crops = [row[0] for row in await cursor.fetchall()]
        
        if len(crops) >= 10:
            print(f"  ✅ {len(crops)} crops available: {', '.join(crops[:5])}...")
            checks_passed += 1
        else:
            print(f"  ⚠️  Only {len(crops)} crops: {crops}")
        
        # CHECK 5: Sample mandi availability
        print("\n✓ Checking mandi coverage...")
        checks_total += 1
        cursor = await conn.execute(
            "SELECT DISTINCT mandi FROM mandi_price_history"
        )
        mandis = [row[0] for row in await cursor.fetchall()]
        
        if len(mandis) >= 20:
            print(f"  ✅ {len(mandis)} mandis available: {', '.join(mandis[:5])}...")
            checks_passed += 1
        else:
            print(f"  ⚠️ Only {len(mandis)} mandis: {mandis}")
        
        # CHECK 6: Test services exist
        print("\n✓ Checking Python services...")
        checks_total += 1
        try:
            from app.services.chat_memory import chat_memory
            from app.services.user_profile import user_profile
            from app.services.gemini_service import gemini_service
            print("  ✅ All services imported successfully")
            checks_passed += 1
        except ImportError as e:
            print(f"  ❌ Service import failed: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return False
    
    # SUMMARY
    print("\n" + "=" * 70)
    print(f"📊 RESULTS: {checks_passed}/{checks_total} checks passed")
    print("=" * 70)
    
    if checks_passed == checks_total:
        print("\n🎉 ALL SYSTEMS GO! Ready for production!")
        return True
    elif checks_passed >= checks_total * 0.8:
        print("\n⚠️  MOSTLY READY - Minor issues to fix")
        return True
    else:
        print("\n❌ CRITICAL ISSUES - Fix before deployment")
        return False


if __name__ == "__main__":
    result = asyncio.run(verify_system())
    sys.exit(0 if result else 1)
