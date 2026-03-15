# Setup Guide — AI Sign Language Translator

## Prerequisites

| Software | Version | Link |
|----------|---------|------|
| **Node.js** | 18+ | https://nodejs.org/ |
| **Python** | 3.10+ | https://python.org/ |
| **Git** | any | https://git-scm.com/ |
| **Docker** (optional) | 20+ | https://www.docker.com/products/docker-desktop |

---

## 1. Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with a Google account
3. Click **Create API Key**
4. Copy the key (starts with `AIza...`)

---

## 2. Clone the Repository

```bash
git clone https://github.com/rakhatdiploma/iitudiplomas.git
cd iitudiplomas
```

---

## Quick Start — Docker (Recommended)

This is the fastest way to get everything running.

### 1. Create the `.env` file in the project root

```bash
cp .env.example .env
```

Open `.env` and paste your Gemini API key:

```
GEMINI_API_KEY=AIza...your_key_here
```

### 2. Build and start all services

```bash
docker-compose up -d --build
```

### 3. Verify

```bash
docker-compose ps
```

All three containers should show `Up`:

| Service | Container | Port |
|---------|-----------|------|
| Frontend | vur-frontend-1 | http://localhost:3001 |
| MediaPipe | vur-media-pipe-1 | http://localhost:8001 |
| LLM Service | vur-llm-service-1 | http://localhost:8002 |

Open **http://localhost:3001** in your browser.

### Useful Docker commands

```bash
docker-compose logs -f              # Stream all logs
docker-compose logs -f media-pipe   # Logs for one service
docker-compose down                 # Stop everything
docker-compose up -d --build        # Rebuild and restart
```

---

## Quick Start — Local Development

Use this if you want hot-reload and direct access to the code.

### Terminal 1 — MediaPipe Service (port 8001)

```bash
cd backend/media_pipe_service
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Terminal 2 — LLM Service (port 8002)

```bash
cd backend/llm_service

# Create .env with your key
cp .env.example .env
# Edit .env → set GEMINI_API_KEY=AIza...

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

### Terminal 3 — Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Environment Variables

### Root `.env` (used by `docker-compose`)

```
GEMINI_API_KEY=your_gemini_api_key_here
```

### `backend/llm_service/.env`

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
PORT=8002
LOG_LEVEL=info
```

### `backend/media_pipe_service/.env`

```
PORT=8001
CONFIDENCE_THRESHOLD=0.7
LLM_SERVICE_URL=http://localhost:8002
DEBUG=true
```

> When running with Docker, the MediaPipe service reaches the LLM service
> via the Docker network name `http://llm-service:8002`. This is set
> automatically in `docker-compose.yml`.

---

## Project Structure

```
VUR/
├── .env                            # Gemini key (for docker-compose)
├── .env.example
├── docker-compose.yml
├── Makefile
├── README.md
├── API_CONTRACTS.md
├── DEVELOPMENT_PLAN.md
├── SETUP_GUIDE.md                  # ← you are here
│
├── frontend/                       # React 19 + TypeScript + Vite
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── Camera.tsx
│       │   ├── Controls.tsx
│       │   ├── StatusBar.tsx
│       │   └── TranslationPanel.tsx
│       ├── hooks/
│       │   ├── useCamera.ts
│       │   └── useWebSocket.ts
│       ├── services/
│       │   └── api.ts
│       ├── store/
│       │   └── useAppStore.ts
│       └── types/
│           └── index.ts
│
└── backend/
    ├── media_pipe_service/         # FastAPI — hand detection
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── .env.example
    │   ├── main.py
    │   └── app/
    │       ├── main.py
    │       ├── config.py
    │       ├── models/
    │       │   ├── gesture_classifier.py
    │       │   └── schemas.py
    │       ├── routers/
    │       │   ├── health.py
    │       │   └── websocket.py
    │       └── services/
    │           ├── hand_detector.py
    │           └── sign_buffer.py
    │
    └── llm_service/                # FastAPI — Gemini translation
        ├── Dockerfile
        ├── requirements.txt
        ├── .env.example
        ├── main.py
        └── app/
            ├── main.py
            ├── config.py
            ├── clients/
            │   └── gemini_client.py
            ├── processors/
            │   └── sentence_builder.py
            ├── context/
            │   └── session_manager.py
            └── routers/
                ├── health.py
                └── translate.py
```

---

## Service URLs

### Local development

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost:5173 | Vite dev server |
| MediaPipe | http://localhost:8001 | WebSocket + health |
| MediaPipe API docs | http://localhost:8001/docs | Swagger UI (DEBUG=true) |
| LLM Service | http://localhost:8002 | REST API |
| LLM API docs | http://localhost:8002/docs | Swagger UI |
| WebSocket | ws://localhost:8001/ws/sign-detection | Real-time detection |

### Docker

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3001 |
| MediaPipe | http://localhost:8001 |
| LLM Service | http://localhost:8002 |

---

## Health Checks

```bash
# MediaPipe
curl http://localhost:8001/api/v1/health

# LLM Service
curl http://localhost:8002/health

# Test LLM translation directly
curl -X POST http://localhost:8002/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"sign_sequence": ["привет", "мир"], "language": "ru"}'
```

---

## Troubleshooting

### Camera not working

- Open **http://localhost:5173** (local) or **http://localhost:3001** (Docker)
- The browser must be Chrome, Firefox, or Edge (Safari has limited support)
- Click the camera/lock icon in the address bar and allow camera access
- If blocked, go to browser settings → Site Settings → Camera → Allow

### `npm install` fails

```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### `ModuleNotFoundError` in Python

```bash
# Make sure the virtualenv is activated
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### `Address already in use`

```bash
# Find what's using the port
lsof -ti:8001 | xargs kill -9    # Linux/Mac
# or pick a different port
uvicorn app.main:app --reload --port 8003
```

### Gemini API errors

- Verify `.env` contains a valid `GEMINI_API_KEY`
- Check the key at https://aistudio.google.com/app/apikey
- The LLM service runs in **fallback mode** (simple concatenation) when no key is set
- Check logs: `docker-compose logs -f llm-service`

### Docker: media-pipe container keeps restarting

```bash
docker-compose logs media-pipe --tail 30
```

Common cause: missing system library. The Dockerfile installs `libgl1` for
OpenCV. If you see `libGL.so.1: cannot open shared object file`, rebuild:

```bash
docker-compose build media-pipe --no-cache
docker-compose up -d
```

---

## Team

| Role | Name | Module | Port |
|------|------|--------|------|
| Frontend | Ulzhan | React + WebSocket Client | 5173 / 3001 |
| Backend | Vlad | MediaPipe Service | 8001 |
| Backend / Team Lead | Rakhat | LLM Service (Gemini) | 8002 |
