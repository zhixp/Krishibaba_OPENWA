"""
PHASE 1: PULSE CHECK - Verify Backend Gold Standard
Tests Silent Onboarding + Fact Injection
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_step(step_name, data, expected_intent=None):
    """Test a step and show results"""
    print(f"\n{'='*70}")
    print(f"STEP: {step_name}")
    print(f"{'='*70}")
    print(f"Request: {json.dumps(data, indent=2)}")
    
    try:
        r = requests.post(f"{BASE_URL}/v1/chat/interact", json=data, timeout=20)
        
        if r.status_code == 200:
            response = r.json()
            print(f"\n✅ SUCCESS (200)")
            print(f"Reply: {response.get('reply_text_hindi', '')[:150]}")
            print(f"Intent: {response.get('intent')}")
            print(f"Location: {response.get('detected_location')}")
            
            if expected_intent and response.get('intent') != expected_intent:
                print(f"⚠️  Expected intent: {expected_intent}")
            
            return response
        else:
            print(f"\n❌ FAILED ({r.status_code})")
            print(f"Error: {r.text[:200]}")
            return None
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        return None

print("\n" + "🔥"*35)
print("PHASE 1: PULSE CHECK - Backend Verification")
print("🔥"*35)

# STEP 1: The Stranger (New User)
step1 = test_step(
    "1. New User - Ram Ram",
    {"uid": "test_user_01", "text_input": "Ram Ram"},
    expected_intent="onboarding_ask_name"
)

# STEP 2: The Identity (Name)
step2 = test_step(
    "2. Provide Name",
    {"uid": "test_user_01", "text_input": "Ramesh Kumar"},
    expected_intent="onboarding_ask_crop"
)

# STEP 3: The Crop
step3 = test_step(
    "3. Provide Crop",
    {"uid": "test_user_01", "text_input": "Soyabean"},
    expected_intent="onboarding_ask_location"
)

# STEP 4: The Anchor (GPS)
step4 = test_step(
    "4. Send GPS Location",
    {
        "uid": "test_user_01",
        "text_input": "",
        "latitude": 23.25,
        "longitude": 77.40
    },
    expected_intent="onboarding_complete"
)

# STEP 5: The Payoff (Weather Query)
step5 = test_step(
    "5. Weather Query (Active User)",
    {"uid": "test_user_01", "text_input": "Mausam kaisa hai?"},
    expected_intent="weather_forecast"
)

# RESULTS SUMMARY
print("\n" + "="*70)
print("RESULTS SUMMARY")
print("="*70)

tests = [
    ("Step 1: New User", step1, "onboarding_ask_name"),
    ("Step 2: Name", step2, "onboarding_ask_crop"),
    ("Step 3: Crop", step3, "onboarding_ask_location"),
    ("Step 4: GPS Location", step4, "onboarding_complete"),
    ("Step 5: Weather Query", step5, "weather_forecast"),
]

all_passed = True
for name, result, expected in tests:
    if result and result.get('intent') == expected:
        print(f"✅ {name} - PASS")
    else:
        print(f"❌ {name} - FAIL")
        all_passed = False

print("\n" + "="*70)
if all_passed:
    print("🎉 BACKEND IS GOLD - All tests passed!")
    print("✅ Silent Onboarding: Working")
    print("✅ State Machine: Working")
    print("✅ Fact Injection: Ready")
    print("\nNext: Phase 2 - WhatsApp/OpenWA Integration")
else:
    print("⚠️  BACKEND NEEDS FIXES - Check logs above")
print("="*70 + "\n")
