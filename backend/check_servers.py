import requests

# Test both servers
ports = [5000, 8000]

for port in ports:
    print(f"\n{'='*60}")
    print(f"Testing server on port {port}")
    print('='*60)
    
    try:
        # Test chat endpoint
        response = requests.post(
            f"http://localhost:{port}/v1/chat/interact",
            json={
                "uid": "quick_test_786",
                "text_input": "464774"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get('reply_text_hindi', '')
            print(f"✅ Server responding")
            print(f"Reply preview: {reply[:150]}...")
            print(f"Intent: {data.get('intent')}")
            
            # Check for old bilingual format
            if '(Wheat)' in reply or '(Quality)' in reply:
                print("❌ OLD CODE - Has bilingual format")
            else:
                print("✅ NEW CODE - Pure Hindi")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Cannot connect: {e}")

print(f"\n{'='*60}")
print("RECOMMENDATION:")
print("='*60")
print("Use the port with NEW CODE for the active WhatsApp/channel backend")
print("Or restart the server you want to use with latest code")
