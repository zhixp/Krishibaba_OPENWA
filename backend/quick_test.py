import requests
import os
from dotenv import load_dotenv

load_dotenv()

url = "http://localhost:8000/v1/broadcast/send"
admin_key = os.getenv("BROADCAST_ADMIN_KEY", "").strip()  # Strip whitespace

# If .env not working, use direct value
if not admin_key:
    admin_key = "SarpanchAI@7007"

data = {
    "admin_key": admin_key,
    "pincode": "all",
    "crop": "all",
    "message_text": "Test message - यह टेस्ट है!"
}

print("Testing broadcast...")
print(f"URL: {url}")
print(f"Admin Key: '{admin_key}'")
print(f"Key Length: {len(admin_key)}")

try:
    r = requests.post(url, json=data, timeout=5)
    print(f"\nStatus: {r.status_code}")
    print(f"Response:\n{r.text}")
except Exception as e:
    print(f"Error: {e}")
