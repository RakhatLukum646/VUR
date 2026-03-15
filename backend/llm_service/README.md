# LLM Service

Natural language translation service for sign language detection.

## Features

- Google Gemini API integration for intelligent translation
- Session-based context management
- REST API for sign sequence translation
- Support for multiple languages

## Setup

1. Copy `.env.example` to `.env` and add your Gemini API key:
```bash
cp .env.example .env
# Edit .env and add GEMINI_API_KEY
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the service:
```bash
uvicorn app.main:app --reload --port 8002
```

## API Endpoints

- `POST /api/v1/translate` - Translate sign sequence
- `POST /api/v1/sessions` - Create new session
- `GET /api/v1/context/{session_id}` - Get session context
- `DELETE /api/v1/context/{session_id}` - Clear session
- `GET /health` - Health check

## Testing

```bash
pytest tests/
```
