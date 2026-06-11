"""
CLEANUP SCRIPT - Remove unnecessary test files
Keep only production-ready tests
"""
import os

# Files to DELETE (old/experimental tests)
DELETE_FILES = [
    "test_ai.py",
    "test_all_phases.py",
    "test_basic.py",
    "test_broadcast.py",
    "test_comprehensive.py",
    "test_context_system.py",
    "test_current_persona.py",
    "test_dev_user.py",
    "test_final_broadcast.py",
    "test_flash_latest.py",
    "test_full_system.py",
    "test_geocoding.py",
    "test_hybrid_geocoding.py",
    "test_key_raw.py",
    "test_library.py",
    "test_onboarding_flow.py",
    "test_phase1.py",
    "test_port5000.py",
    "test_scraper.py",
    "test_scraper_offline.py",
    "test_simple.py",
    "test_simple_broadcast.py",
]

# Files to KEEP (production tests)
KEEP_FILES = [
    "test_agmarknet.py",  # Mandi API test
    "test_gemini.py",     # AI test
    "emergency_test.py",  # Production readiness test
    "pulse_check.py",     # Backend verification
]

def cleanup():
    deleted = 0
    errors = []
    
    print("="*70)
    print("🧹 CLEANUP - Removing Unnecessary Test Files")
    print("="*70)
    
    for filename in DELETE_FILES:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"✅ Deleted: {filename}")
                deleted += 1
            except Exception as e:
                print(f"❌ Error deleting {filename}: {e}")
                errors.append(filename)
        else:
            print(f"⏭️  Not found: {filename}")
    
    print("\n" + "="*70)
    print(f"✅ Cleanup Complete: {deleted} files deleted")
    if errors:
        print(f"⚠️  Errors: {len(errors)} files")
    
    print("\n📁 Keeping these production tests:")
    for filename in KEEP_FILES:
        if os.path.exists(filename):
            print(f"   ✓ {filename}")
    print("="*70)

if __name__ == "__main__":
    cleanup()
