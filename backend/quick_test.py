import os

import requests
from dotenv import load_dotenv


load_dotenv()

url = "http://localhost:8000/v1/broadcast/send"
admin_key = (os.getenv("BROADCAST_ADMIN_KEY") or os.getenv("ADMIN_API_KEY") or "").strip()

if not admin_key:
    raise RuntimeError("Set BROADCAST_ADMIN_KEY or ADMIN_API_KEY before running this test")

data = {
    "pincode": "all",
    "crop": "all",
    "message_text": "Test broadcast message",
}
headers = {"X-API-Key": admin_key}

print("Testing broadcast...")
print(f"URL: {url}")
print(f"Admin Key Length: {len(admin_key)}")

try:
    response = requests.post(url, json=data, headers=headers, timeout=5)
    print(f"\nStatus: {response.status_code}")
    print(f"Response:\n{response.text}")
except Exception as exc:
    print(f"Error: {exc}")
