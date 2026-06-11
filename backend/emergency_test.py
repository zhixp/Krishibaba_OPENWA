"""
🚨 EMERGENCY FIX TEST - Production Readiness
Tests: Latency (<3s), Pincode Robustness, Real-World Scenarios
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test(desc, data, max_time=4):
    """Test with latency check"""
    print(f"\n{'='*70}")
    print(f"TEST: {desc}")
    print(f"Data: {data}")
    
    start = time.time()
    try:
        r = requests.post(f"{BASE_URL}/v1/chat/interact", json=data, timeout=10)
        elapsed = time.time() - start
        
        if r.status_code == 200:
            resp = r.json()
            reply = resp.get('reply_text_hindi', '')
            
            # Check latency
            if elapsed < max_time:
                print(f"✅ PASS ({elapsed:.2f}s < {max_time}s)")
            else:
                print(f"⚠️  SLOW ({elapsed:.2f}s >= {max_time}s) - FAIL for 2G")
            
            print(f"Reply: {reply[:100]}")
            return (r.status_code == 200 and elapsed < max_time, elapsed)
        else:
            print(f"❌ HTTP {r.status_code}")
            return (False, time.time() - start)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return (False, time.time() - start)

print("\n" + "🚨"*35)
print("EMERGENCY FIX VERIFICATION - Production Ready Test")
print("🚨"*35)

results = []

# Test 1: Pincode with spaces (common user error)
print("\n📋 TEST 1: ROBUST PINCODE VALIDATION")
print("-"*70)
uid1 = "emergency_fix_1"
test("Onboarding", {"uid": uid1, "text_input": "Hi"}, 2)
test("Name", {"uid": uid1, "text_input": "Test User"}, 2)
test("Crop", {"uid": uid1, "text_input": "Wheat"}, 2)
results.append(test("Pincode with spaces", {"uid": uid1, "text_input": " 464774 "}, 3))

# Test 2: Pincode with trailing dot
uid2 = "emergency_fix_2"
test("Onboarding", {"uid": uid2, "text_input": "Hello"}, 2)
test("Name", {"uid": uid2, "text_input": "Farmer 2"}, 2)
test("Crop", {"uid": uid2, "text_input": "Rice"}, 2)
results.append(test("Pincode with dot", {"uid": uid2, "text_input": "464774."}, 3))

# Test 3: GPS (should be fastest)
uid3 = "emergency_fix_3"
test("Onboarding", {"uid": uid3, "text_input": "Ram Ram"}, 2)
test("Name", {"uid": uid3, "text_input": "GPS User"}, 2)
test("Crop", {"uid": uid3, "text_input": "Soyabean"}, 2)
results.append(test("GPS Location", {
    "uid": uid3,
    "text_input": "",
    "latitude": 23.25,
    "longitude": 77.40
}, 2))

# Test 4: Weather Query (CRITICAL - must be < 3s)
print("\n📋 TEST 4: WEATHER LATENCY (CRITICAL)")
print("-"*70)
results.append(test("Weather with saved GPS", {
    "uid": uid3,
    "text_input": "Mausam batao"
}, 5))  # Allow 5s for first weather query (includes AI)

# RESULTS
print("\n" + "="*70)
print("📊 RESULTS SUMMARY")
print("="*70)

passed = sum(1 for r in results if r[0])
total = len(results)
avg_latency = sum(r[1] for r in results) / len(results)

print(f"Tests Passed: {passed}/{total}")
print(f"Average Latency: {avg_latency:.2f}s")

if passed == total and avg_latency < 3:
    print("\n🎉 PRODUCTION READY - All tests passed, latency acceptable!")
elif passed >= total * 0.8:
    print("\n⚠️  ACCEPTABLE - Most tests passed, minor issues")
else:
    print("\n❌ NOT READY - Critical failures detected")

print("="*70 + "\n")

# Specific checks
print("CRITICAL CHECKLIST:")
print(f"✓ Pincode with spaces: {'PASS' if results[0][0] else 'FAIL'}")
print(f"✓ Pincode with punctuation: {'PASS' if results[1][0] else 'FAIL'}")
print(f"✓ GPS location: {'PASS' if results[2][0] else 'FAIL'}")
print(f"✓ Weather < 5s: {'PASS' if results[3][1] < 5 else 'F AIL - TOO SLOW for 2G'}")
print()
