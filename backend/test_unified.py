import requests

# Test the unified chat endpoint
url = "http://localhost:8000/v1/unified/chat"

# Test 1: Simple greeting
print("=" * 50)
print("Test 1: Simple Greeting")
print("=" * 50)
response = requests.post(url, data={
    "uid": "test_user_123",
    "message": "Namaste"
})
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 2: Weather query
print("=" * 50)
print("Test 2: Weather Query")
print("=" * 50)
response = requests.post(url, data={
    "uid": "test_user_123",
    "message": "Kal barish hogi?"
})
print(f"Status: {response.status_code}")
result = response.json()
print(f"Intent: {result.get('intent')}")
print(f"Data fetched: {result.get('data_fetched')}")
print(f"Reply: {result.get('reply')}\n")

# Test 3: Mandi query
print("=" * 50)
print("Test 3: Mandi Query")
print("=" * 50)
response = requests.post(url, data={
    "uid": "test_user_123",
    "message": "Soybean ka bhav kya hai?"
})
print(f"Status: {response.status_code}")
result = response.json()
print(f"Intent: {result.get('intent')}")
print(f"Data fetched: {result.get('data_fetched')}")
print(f"Reply: {result.get('reply')}\n")

# Test 4: Complex decision (should trigger both)
print("=" * 50)
print("Test 4: Complex Decision Query")
print("=" * 50)
response = requests.post(url, data={
    "uid": "test_user_123",
    "message": "Aaj mandi jaun ya kal jaun?"
})
print(f"Status: {response.status_code}")
result = response.json()
print(f"Intent: {result.get('intent')}")
print(f"Data fetched: {result.get('data_fetched')}")
print(f"Reply: {result.get('reply')}\n")

print("=" * 50)
print("✅ All tests complete!")
print("=" * 50)
