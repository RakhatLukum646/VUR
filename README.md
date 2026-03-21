# AI Sign Language Translator

Real-time sign language to text translation using MediaPipe, Google Gemini, and a trained MLP classifier.

## Team

| Role | Name | Module |
|------|------|--------|
| Frontend | Ulzhan | React + WebSocket Client |
| Backend | Vlad | MediaPipe Service |
| Backend / Teamlead | Rakhat | LLM Service + Architecture |

---

## Architecture

All traffic goes through a single **Nginx API Gateway** on port 80.

```
Browser
  │
  ▼
┌─────────────────────────────────────┐
│   Nginx Gateway  :80                │
│  /        → Frontend (React)        │
│  /ws/     → MediaPipe (WebSocket)   │
│  /api/v1/ → LLM Service (REST)      │
│  /auth/   → Auth Service (REST)     │
└────────────────┬────────────────────┘
                 │ internal Docker network
    ┌────────────┼─────────────┐
    ▼            ▼             ▼
 Frontend    MediaPipe       LLM
  :80          :8001         :8002
                 │
                 └──(HTTP)──► LLM :8002
                              (Gemini API)
```

---

## Services

### Frontend — React + TypeScript
- Live camera feed with **hand skeleton overlay** drawn on canvas
- Real-time detected signs stream
- Gemini-powered sentence translation
- **Language selector** (English / Russian / Kazakh)
- **Toast notifications** for errors, fallback mode, and translation results
- Auth: register, login, 2FA, email verification, profile management

### MediaPipe Service — Port 8001
- FastAPI WebSocket server
- Real-time hand landmark detection (21 points via MediaPipe)
- **ML-based gesture classifier** (MLP, falls back to heuristics)
- Smart sign segmentation: auto-commits sequence when hand drops (rest detection)
- Sign sequence buffer with 500 ms debounce
- WebSocket: `ws://localhost:8001/ws/sign-detection`

### LLM Service — Port 8002
- Google Gemini API integration
- Converts raw sign sequences / fingerspelling into grammatically correct sentences
- Multi-language support: English, Russian, Kazakh
- Session-based conversation context
- Graceful fallback when Gemini API is unavailable
- Docs: `http://localhost:8002/docs`

### Auth Service — Port 8003
- JWT authentication
- Email verification
- Two-factor authentication (TOTP)
- User profile management

---

## Quick Start

### Docker (recommended)

```bash
# 1. Copy and fill in secrets
cp .env.example .env
# Set GEMINI_API_KEY, MongoDB credentials, email settings

# 2. Start everything
docker compose up --build

# App is available at http://localhost
```

### Local Development

```bash
# Copy local dev env vars for the frontend
cp frontend/.env.local.example frontend/.env.local
# Edit .env.local and set your local service URLs

# Terminal 1 — Auth Service
cd backend/auth_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003

# Terminal 2 — MediaPipe Service
cd backend/media_pipe_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Terminal 3 — LLM Service
cd backend/llm_service
cp .env.example .env   # add GEMINI_API_KEY
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# Terminal 4 — Frontend
cd frontend
npm install
npm run dev            # http://localhost:5173
```

Or with Make:

```bash
make dev
```

---

## ML Gesture Classifier

The MediaPipe service ships with a geometry-based heuristic classifier as fallback.  
To train the full MLP model on your own data:

```bash
cd backend/media_pipe_service

# 1. Collect training samples for each sign (repeat for every letter/gesture)
python scripts/record_training_data.py --label A --samples 200
python scripts/record_training_data.py --label B --samples 200
# ...

# 2. Train the MLP classifier
python scripts/train_classifier.py

# The trained model is saved to data/gesture_model.pkl
# The service loads it automatically on startup.
```

## Evaluation And Benchmarks

The repository now includes reproducible evaluation tooling for both the
classifier and the translation service.

```bash
# Classifier metrics + confusion matrix
cd backend/media_pipe_service
source venv/bin/activate
python scripts/evaluate_classifier.py --data data/landmarks.csv --out-dir reports

# Translation latency + keyword quality baseline
cd ../llm_service
source venv/bin/activate
python scripts/benchmark_translation.py --cases evaluation/translation_cases.json --out reports/translation_benchmark.json
```

Generated artifacts:
- `backend/media_pipe_service/reports/classifier_metrics.json`
- `backend/media_pipe_service/reports/confusion_matrix.csv`
- `backend/llm_service/reports/translation_benchmark.json`

See `docs/evaluation.md` for the recommended defense-ready workflow.

---

## Environment Variables

Create a `.env` file in the project root (or use `.env.example` as a template):

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `MONGODB_URL` | Yes | MongoDB connection string |
| `MONGODB_DB` | Yes | MongoDB database name |
| `JWT_SECRET` | Yes | Secret for signing JWT tokens |
| `EMAIL_HOST` | Yes | SMTP host for verification emails |
| `EMAIL_PORT` | Yes | SMTP port |
| `EMAIL_USER` | Yes | SMTP username |
| `EMAIL_PASSWORD` | Yes | SMTP password |

For local frontend development, copy `frontend/.env.local.example` to `frontend/.env.local`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_LLM_URL` | `http://localhost:8002` | LLM service URL |
| `VITE_AUTH_URL` | `http://localhost:8003` | Auth service URL |
| `VITE_WS_URL` | `ws://localhost:8001` | MediaPipe WebSocket URL |

---

## How to Use

1. Open `http://localhost` and sign in (or register)
2. Allow camera access when prompted
3. Select your **target language** (English / Russian / Kazakh)
4. Click **Start Translation**
5. Make ASL hand gestures — the skeleton overlay confirms the camera sees your hand
6. Detected signs appear in the panel in real-time
7. Translation fires automatically when you lower your hand (rest detection), or click **Translate Signs to Sentence**
8. Click **Clear** to start a new session

---

## Project Status

| Component | Status |
|-----------|--------|
| Auth Service | Complete |
| MediaPipe Hand Detection | Complete |
| Gesture Classifier (heuristic) | Complete |
| Gesture Classifier (ML/MLP) | Complete — requires training data |
| LLM Translation (Gemini) | Complete |
| Frontend UI | Complete |
| Landmark Overlay | Complete |
| Language Selection | Complete |
| API Gateway (Nginx) | Complete |
| Docker Compose | Complete |

---

## Repository

https://github.com/RakhatLukum646/VUR
