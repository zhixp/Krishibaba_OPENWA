# Krishi Baba Backend

FastAPI backend for Krishi Baba - AI-powered agricultural assistant for rural India.

## Features (Phase 1)
- ✅ RESTful API with FastAPI
- ✅ SQLite database (async with aiosqlite)
- ✅ Configurable AI prompts (YAML)
- ✅ User registration and chat endpoint
- ✅ Offline data sync endpoint
- ✅ Admin data ingestion API
- 🚧 Gemini AI integration (Phase 2)
- 🚧 Voice/audio support (Phase 4)

## Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Run Development Server
```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. View API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── config.py        # Settings & environment variables
│   │   ├── prompts.yaml     # AI prompts (EDITABLE!)
│   │   └── prompt_manager.py # Prompt loader with hot-reload
│   ├── database/
│   │   └── db.py            # Database schema & connection
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── routers/
│       ├── chat.py          # Chat interaction endpoints
│       ├── sync.py          # Offline sync endpoints
│       └── admin.py         # Admin/ingestion endpoints
├── requirements.txt
└── .env.example
```

## API Endpoints

### Public Endpoints
- `GET /` - Health check
- `POST /v1/chat/interact` - Main chat interaction (text-only in Phase 1)
- `POST /v1/chat/register` - User registration after Google Sign-In
- `GET /v1/sync/data` - Offline data sync

### Admin Endpoints (Require API Key)
- `POST /v1/admin/ingest/mandi` - Bulk insert mandi prices
- `POST /v1/admin/ingest/schemes` - Bulk insert government schemes
- `POST /v1/admin/reload-prompts` - Hot-reload AI prompts

## Editing AI Prompts

Edit `app/core/prompts.yaml` to change AI behavior. You can:
1. Modify prompt templates
2. Adjust temperature and max_tokens
3. Add new prompt types

To apply changes without restarting:
```bash
curl -X POST http://localhost:8000/v1/admin/reload-prompts \
  -H "X-API-Key: your_admin_key"
```

## Next Steps (Phase 2)
- [ ] Integrate Gemini AI service
- [ ] Implement intent classification
- [ ] Add location extraction from Hindi text
- [ ] Connect real mandi price data

## Production Deployment
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
