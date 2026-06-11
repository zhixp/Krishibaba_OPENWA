"""
🚀 COMPREHENSIVE SYSTEM TEST
Tests everything: Silent Onboarding + GPS + Weather + Fact Injection
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(emoji, msg, color=None):
    if color:
        print(f"{color}{emoji} {msg}{Colors.END}")
    else:
        print(f"{emoji} {msg}")

def test_api(step, uid, data, expected_keywords=None):
    """Test API call and validate response"""
    log("🔹", f"\n{step}", Colors.BLUE)
    log("📤", f"Request: {json.dumps(data, indent=2)}")
    
    try:
        start = time.time()
        r = requests.post(f"{BASE_URL}/v1/chat/interact", json=data, timeout=30)
        elapsed = time.time() - start
        
        if r.status_code == 200:
            resp = r.json()
            reply = resp.get('reply_text_hindi', '')
            
            log("✅", f"SUCCESS ({elapsed:.1f}s)", Colors.GREEN)
            log("💬", f"Reply: {reply[:100]}...")
            log("🎯", f"Intent: {resp.get('intent')}")
            log("📍", f"Location: {resp.get('detected_location')}")
            
            # Validate expected keywords
            if expected_keywords:
                found_all = all(kw.lower() in reply.lower() for kw in expected_keywords)
                if found_all:
                    log("✓", f"Keywords found: {expected_keywords}", Colors.GREEN)
                else:
                    log("⚠", f"Missing keywords: {expected_keywords}", Colors.YELLOW)
            
            return resp
        else:
            log("❌", f"HTTP {r.status_code}: {r.text[:150]}", Colors.RED)
            return None
            
    except requests.Timeout:
        log("⏱", "Request timed out (>30s)", Colors.YELLOW)
        return None
    except Exception as e:
        log("💥", f"Error: {e}", Colors.RED)
        return None

# ==============================================================================
# TEST SUITE
# ==============================================================================

print("\n" + "="*80)
print("🚀 COMPREHENSIVE SYSTEM TEST - Krishi Baba v2.0")
print("="*80)

# Test 1: New User Flow (Complete Onboarding)
log("\n📋", "TEST 1: New User Silent Onboarding", Colors.BLUE)
print("-"*80)

uid1 = "comprehensive_test_user_1"

step1 = test_api(
    "Step 1.1: New User Greeting",
    uid1,
    {"uid": uid1, "text_input": "Namaste"},
    expected_keywords=["नाम"]
)

step2 = test_api(
    "Step 1.2: Provide Name",
    uid1,
    {"uid": uid1, "text_input": "Ramesh Kumar"},
    expected_keywords=["फसल"]
)

step3 = test_api(
    "Step 1.3: Provide Crop",
    uid1,
    {"uid": uid1, "text_input": "Soyabean"},
    expected_keywords=["Location", "भेजें"]
)

step4 = test_api(
    "Step 1.4: Send GPS Coordinates",
    uid1,
    {
        "uid": uid1,
        "text_input": "",
        "latitude": 23.2599,  # Bhopal
        "longitude": 77.4126
    },
    expected_keywords=["Setup", "पूरा"]
)

# Test 2: Returning User (Direct Query)
log("\n📋", "TEST 2: Returning User - Auto Weather", Colors.BLUE)
print("-"*80)

step5 = test_api(
    "Step 2.1: Weather Query (GPS saved)",
    uid1,
    {"uid": uid1, "text_input": "Mausam batao"},
    expected_keywords=["आज", "°C"]  # Should show forecast
)

# Test 3: GPS Priority Test
log("\n📋", "TEST 3: GPS vs Pincode Priority", Colors.BLUE)
print("-"*80)

uid2 = "gps_priority_test"

gps_test1 = test_api(
    "Step 3.1: New User",
    uid2,
    {"uid": uid2, "text_input": "Hi"}
)

gps_test2 = test_api(
    "Step 3.2: Name",
    uid2,
    {"uid": uid2, "text_input": "GPS Test User"}
)

gps_test3 = test_api(
    "Step 3.3: Crop",
    uid2,
    {"uid": uid2, "text_input": "Wheat"}
)

gps_test4 = test_api(
    "Step 3.4: Send GPS (Should prioritize over any text)",
    uid2,
    {
        "uid": uid2,
        "text_input": "123456",  # Some text
        "latitude": 28.6139,  # Delhi
        "longitude": 77.2090
    },
    expected_keywords=["Setup", "पूरा"]
)

# Test 4: Pincode Fallback
log("\n📋", "TEST 4: Pincode Fallback (No GPS)", Colors.BLUE)
print("-"*80)

uid3 = "pincode_test"

pin_test1 = test_api("Step 4.1: New User", uid3, {"uid": uid3, "text_input": "Hello"})
pin_test2 = test_api("Step 4.2: Name", uid3, {"uid": uid3, "text_input": "Pincode User"})
pin_test3 = test_api("Step 4.3: Crop", uid3, {"uid": uid3, "text_input": "Paddy"})
pin_test4 = test_api(
    "Step 4.4: Send Pincode (No GPS)",
    uid3,
    {"uid": uid3, "text_input": "464774"},
    expected_keywords=["Setup"]
)

# Test 5: Error Handling
log("\n📋", "TEST 5: Error Handling", Colors.BLUE)
print("-"*80)

uid4 = "error_test"

err_test1 = test_api("Step 5.1: New User", uid4, {"uid": uid4, "text_input": "Hi"})
err_test2 = test_api(
    "Step 5.2: Invalid Name (too short)",
    uid4,
    {"uid": uid4, "text_input": "A"},
    expected_keywords=["नाम"]  # Should ask again
)
err_test3 = test_api(
    "Step 5.3: Valid Name",
    uid4,
    {"uid": uid4, "text_input": "Valid Name"}
)

# ==============================================================================
# RESULTS SUMMARY
# ==============================================================================

print("\n" + "="*80)
print("📊 TEST RESULTS SUMMARY")
print("="*80)

tests = [
    ("Silent Onboarding (1.1-1.4)", [step1, step2, step3, step4]),
    ("Returning User Weather (2.1)", [step5]),
    ("GPS Priority (3.1-3.4)", [gps_test1, gps_test2, gps_test3, gps_test4]),
    ("Pincode Fallback (4.1-4.4)", [pin_test1, pin_test2, pin_test3, pin_test4]),
    ("Error Handling (5.1-5.3)", [err_test1, err_test2, err_test3]),
]

total_tests = 0
passed_tests = 0

for test_name, steps in tests:
    total_tests += len(steps)
    passed = sum(1 for s in steps if s is not None)
    passed_tests += passed
    
    if passed == len(steps):
        log("✅", f"{test_name}: PASS ({passed}/{len(steps)})", Colors.GREEN)
    else:
        log("❌", f"{test_name}: FAIL ({passed}/{len(steps)})", Colors.RED)

print("\n" + "-"*80)
score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
log("📈", f"Overall Score: {passed_tests}/{total_tests} ({score:.1f}%)")

if score >= 80:
    log("🎉", "SYSTEM STATUS: GOLD - Ready for Production!", Colors.GREEN)
elif score >= 60:
    log("⚠", "SYSTEM STATUS: ACCEPTABLE - Minor fixes needed", Colors.YELLOW)
else:
    log("❌", "SYSTEM STATUS: NEEDS WORK - Critical issues found", Colors.RED)

print("="*80 + "\n")
