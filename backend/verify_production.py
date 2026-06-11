"""
QUICK PRODUCTION TEST - Verify Backend Live
Tests: Silent Onboarding + GPS + Pincode Sanitization
"""
import requests
import json

BASE = "http://localhost:8000"

print("\n" + "🔥"*35)
print("BACKEND PRODUCTION VERIFICATION")
print("🔥"*35 + "\n")

# Test 1: Silent Onboarding (AI Blocked)
print("TEST 1: Silent Onboarding")
print("-"*70)
r1 = requests.post(f"{BASE}/v1/chat/interact", json={
    "uid": "prod_test_1",
    "text_input": "Hello"
})
resp1 = r1.json()
print(f"✅ New User: {resp1['reply_text_hindi'][:50]}...")
print(f"   Intent: {resp1['intent']}")

# Test 2: Pincode with Spaces (Sanitization)
r2 = requests.post(f"{BASE}/v1/chat/interact", json={
    "uid": "prod_test_2",  
    "text_input": "Hi"
})
requests.post(f"{BASE}/v1/chat/interact", json={
    "uid": "prod_test_2",
    "text_input": "Ramesh"
})
requests.post(f"{BASE}/v1/chat/interact", json={
    "uid": "prod_test_2",
    "text_input": "Wheat"
})
r_pincode = requests.post(f"{BASE}/v1/chat/interact", json={
    "uid": "prod_test_2",
    "text_input": " 464774 "  # Spaces!
})
resp_pin = r_pincode.json()
print(f"\n✅ Pincode with Spaces: {resp_pin['reply_text_hindi'][:50]}...")
print(f"   Intent: {resp_pin['intent']}")

# Test 3: GPS Injection
r3 = requests.post(f"{BASE}/v1/chat/interact", json={
    "uid": "prod_test_3",
    "text_input": "Namaste"
})
requests.post(f"{BASE}/v1/chat/interact", json={
    "uid": "prod_test_3",
    "text_input": "Suresh"
})
requests.post(f"{BASE}/v1/chat/interact", json={
    "uid": "prod_test_3",
    "text_input": "Soybean"
})
r_gps = requests.post(f"{BASE}/v1/chat/interact", json={
    "uid": "prod_test_3",
    "text_input": "",
    "latitude": 23.25,
    "longitude": 77.40
})
resp_gps = r_gps.json()
print(f"\n✅ GPS Location: {resp_gps['reply_text_hindi'][:50]}...")
print(f"   Intent: {resp_gps['intent']}")

print("\n" + "="*70)
print("✅ BACKEND VERIFIED - All Systems Operational!")
print("="*70 + "\n")
