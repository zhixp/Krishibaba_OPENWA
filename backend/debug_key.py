import os
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")

print(f"Key repr: {repr(api_key)}")
print(f"Key length: {len(api_key) if api_key else 'None'}")
print(f"Key bytes: {api_key.encode('utf-8') if api_key else 'None'}")
print(f"Stripped length: {len(api_key.strip()) if api_key else 'None'}")

if api_key:
    print(f"\nFirst 10 chars: {repr(api_key[:10])}")
    print(f"Last 10 chars: {repr(api_key[-10:])}")
    
    # Check for hidden characters
    if '\n' in api_key:
        print("⚠️ WARNING: Newline found in key!")
    if '\r' in api_key:
        print("⚠️ WARNING: Carriage return found in key!")
    if ' ' in api_key:
        print("⚠️ WARNING: Space found in key!")
