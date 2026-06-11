import requests
import json

print("Testing weather endpoint...")

response = requests.post(
    "http://localhost:8000/v1/weather/report",
    data={"uid": "test_user_123", "pincode": "462001"}
)

print(f"Status: {response.status_code}")
print(f"\nResponse JSON:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
