# 🤟 AI Sign Language Translator

Real-time sign language to text translation using MediaPipe and Google Gemini.

## Team

| Role | Name | Module |
|------|------|--------|
| Frontend | Ulzhan | React + WebSocket Client |
| Backend | Vlad | MediaPipe Service (port 8001) |
| Backend/Teamlead | Rakhat (Ans_n0202) | LLM Service (port 8002) |

## Project Status

| Component | Status | Port |
|-----------|--------|------|
| ✅ MediaPipe Service | **COMPLETE** - Vlad | 8001 |
| ✅ LLM Service | **COMPLETE** - Rakhat | 8002 |
| ⏳ Frontend WebSocket | **PENDING** - Ulzhan | 5173 |
| ⏳ Integration Testing | **PENDING** | - |

## Services

### 1. MediaPipe Service (Vlad) - Port 8001
- FastAPI WebSocket server
- Real-time hand landmark detection (21 points)
- Gesture classifier (ASL A-Z, 0-9)
- Sign sequence buffer with debouncing
- WebSocket: `ws://localhost:8001/ws/sign-detection`

### 2. LLM Service (Rakhat) - Port 8002
- Google Gemini API integration
- Natural language translation from sign sequences
- Session-based context management
- REST API endpoints
- Health check: `http://localhost:8002/health`
- API Docs: `http://localhost:8002/docs`

### 3. Frontend (Ulzhan) - Port 5173
- React + TypeScript
- WebSocket client for real-time translation
- Camera component with MediaDevices API
- **PENDING**: WebSocket connection to MediaPipe

## Quick Start

```bash
# 1. MediaPipe Service (Terminal 1)
cd backend/media_pipe_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# 2. LLM Service (Terminal 2)
cd backend/llm_service
cp .env.example .env  # Add GEMINI_API_KEY
touch .env  # Create empty if no key (fallback mode)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# 3. Frontend (Terminal 3)
cd frontend
npm install
npm run dev
```

## API Flow

```
┌──────────┐    WebSocket     ┌──────────────┐    HTTP     ┌──────────┐
│ Frontend │ ───────────────► │ MediaPipe    │ ──────────► │ LLM      │
│          │ ◄─────────────── │ (Port 8001)  │            │ (Port    │
│ (React)  │   Sign detected  │              │            │  8002)   │
└──────────┘                  └──────────────┘            └──────────┘
```

## Next Steps

1. **Ulzhan**: Build WebSocket client in Frontend
   - Connect to `ws://localhost:8001/ws/sign-detection`
   - Send camera frames
   - Display detected signs
   - Call LLM API for translation

2. **Integration Testing**
   - Test full flow: Camera → MediaPipe → LLM → Display

## Links

- Repository: https://github.com/rakhatdiploma/iitudiplomas
