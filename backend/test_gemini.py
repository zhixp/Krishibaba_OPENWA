import os
from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai

api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is required")

genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

response = model.generate_content("नमस्ते! कैसे हैं आप?")

print("Response:", response.text)
