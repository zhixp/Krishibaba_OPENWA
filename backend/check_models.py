import google.generativeai as genai
import os

# Load API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Available Gemini Models:")
print("=" * 50)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        
print("\n" + "=" * 50)
print("Testing models...")

# Test a few common ones
test_models = [
    "gemini-1.5-pro",
    "gemini-1.5-flash", 
    "gemini-2.0-flash-exp",
    "models/gemini-1.5-pro",
    "models/gemini-1.5-flash",
    "models/gemini-2.0-flash-exp"
]

for model_name in test_models:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'OK'")
        print(f"✅ {model_name} - WORKS")
    except Exception as e:
        print(f"❌ {model_name} - {str(e)[:80]}")
