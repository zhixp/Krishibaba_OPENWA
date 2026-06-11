"""
Test backend endpoints directly
"""
import requests
import json

BASE_URL = "http://localhost:8000/v1"

print("=" * 60)
print("🧪 TESTING BACKEND ENDPOINTS")
print("=" * 60)

# Test weather
print("\n1. Testing Weather endpoint...")
try:
    response = requests.post(
        f"{BASE_URL}/weather/report",
        data={"uid": "test123", "pincode": "462001"}  # Bhopal pincode
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test mandi
print("\n2. Testing Mandi endpoint...")
try:
    response = requests.post(
        f"{BASE_URL}/mandi/prices",
        data={"uid": "test123", "crop": "Wheat"}
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success')}")
    print(f"Crop: {result.get('crop')}")
    print(f"Prices count: {len(result.get('prices', []))}")
    if result.get('prices'):
        print(f"First price: {result['prices'][0]}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
