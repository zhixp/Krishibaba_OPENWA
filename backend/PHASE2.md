# Phase 2: AI Integration - Quick Start

## 🎯 What's New in Phase 2

Phase 2 adds full **Google Gemini AI** integration for intelligent conversation handling!

### Features Added
- ✅ Intent classification (mandi/weather/scheme/general)
- ✅ Location extraction from Hindi/Hinglish text
- ✅ Context-aware response generation
- ✅ Mandi price explanation with AI
- ✅ General agricultural advice

---

## 🚀 Setup & Testing

### 1. Install Dependencies (if not done already)
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Gemini API Key
```bash
# Edit .env file and add your Gemini API key
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

**Get API Key:** https://makersuite.google.com/app/apikey

### 3. Seed Sample Data
```bash
python seed_data.py
```

This adds:
- 280 mandi price records (7 days × 8 crops × 5 locations)
- 5 government schemes
- 2 test users

### 4. Test AI Integration
```bash
python test_ai.py
```

This will test:
- ✅ Gemini API connection
- ✅ Intent classification accuracy
- ✅ Location extraction
- ✅ General advice generation

### 5. Start the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Test with Swagger UI

Open: **http://localhost:8000/docs**

Try these queries via `/v1/chat/interact`:

**Mandi Price Query:**
```json
{
  "uid": "test_user_1",
  "text_input": "Bhopal ka gehun ka bhav kya hai?"
}
```

**General Advice:**
```json
{
  "uid": "test_user_1",
  "text_input": "Gehu mein kala dana rog ka ilaj batao"
}
```

**Weather Query:**
```json
{
  "uid": "test_user_1",
  "text_input": "Aaj ka mausam kaisa rahega?"
}
```

---

## 🧠 How It Works

### Intent Classification Flow

1. **User sends message** → "Bhopal ka gehun ka bhav kya hai?"

2. **Gemini AI analyzes** using `context_router` prompt:
   - Detects intent: `mandi`
   - Extracts location: `Bhopal`
   - Generates initial response

3. **Backend fetches data** from `mandi_prices` table

4. **Gemini explains** using `mandi_explainer` prompt:
   - Takes raw price data
   - Generates friendly Hindi response
   - Returns to user

### Configurable Prompts

All AI behavior is controlled by [`app/core/prompts.yaml`](app/core/prompts.yaml):

```yaml
prompts:
  context_router:
    temperature: 0.3
    template: |
      You are Krishi Baba...
      
  mandi_explainer:
    temperature: 0.2
    template: |
      Explain prices to farmer...
```

**Update prompts live:**
```bash
curl -X POST http://localhost:8000/v1/admin/reload-prompts \
  -H "X-API-Key: your_admin_key"
```

---

## 📊 Testing Results

After running `python test_ai.py`, you should see:

```
✅ Gemini API connected successfully!
✅ Intent classification: 4/4 passed
✅ Location extraction: 3/3 passed
✅ General advice generation: working
```

If tests fail, check:
- `.env` has valid `GEMINI_API_KEY`
- Internet connection is working
- No rate limiting (free tier has limits)

---

## 🎨 Customizing AI Behavior

### Make AI More Creative
Edit `prompts.yaml`:
```yaml
general_advisor:
  temperature: 0.7  # Higher = more creative (0.0-1.0)
```

### Change Response Length
```yaml
mandi_explainer:
  max_tokens: 150  # Shorter responses
```

### Adjust Prompts
Modify the `template` fields in `prompts.yaml` to change how AI responds.

Then reload:
```bash
curl -X POST http://localhost:8000/v1/admin/reload-prompts \
  -H "X-API-Key: $ADMIN_API_KEY"
```

---

## 🐛 Troubleshooting

### "Gemini API error: 400"
- Check API key is valid
- Ensure no typos in `.env`

### "Failed to parse JSON response"
- AI might be returning non-JSON
- Check `prompts.yaml` template has proper JSON format instruction
- Try increasing temperature slightly

### Intents are misclassified
- Adjust `context_router` prompt in `prompts.yaml`
- Add more examples in the prompt
- Increase or decrease temperature

---

## 📝 Next Steps

Phase 2 is complete! Ready for:

**Phase 3: Data Services**
- Real-time mandi price scraping
- Weather API integration
- Government schemes updater

**Phase 4: Voice & Audio**
- Audio upload handling
- Gemini audio transcription
- Opus codec optimization

---

## 🎉 Phase 2 Complete!

You now have a fully functional AI-powered agricultural assistant backend that:
- Understands Hindi/Hinglish queries
- Classifies intents accurately
- Fetches and explains mandi prices
- Provides agricultural advice

**Test it now:** `uvicorn app.main:app --reload` → http://localhost:8000/docs
