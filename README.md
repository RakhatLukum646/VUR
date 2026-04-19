# VUR — AI Sign Language Translator

Real-time **Russian Sign Language (RSL)** to text translation using MediaPipe hand detection, a temporal S3D neural network (1,598 RSL word classes), and Google Gemini for natural language output.

## Team

| Role | Name | Module |
|------|------|--------|
| Frontend | Ulzhan | React + WebSocket Client |
| Backend | Vlad | MediaPipe Service |
| Backend / Teamlead | Rakhat | LLM Service + Architecture |

---

## How It Works

The pipeline has three stages:

```
1. Hand Detection       2. Sign Classification     3. LLM Translation
─────────────────       ──────────────────────     ──────────────────
Camera frame            32-frame sliding window    Gemini 2.5 Flash
    ↓                       ↓                          ↓
MediaPipe Hands         S3D ONNX model             Grammatically correct
21 landmarks            1,598 RSL classes           Russian sentence
```

### Stage 1 — Hand Detection (MediaPipe)

The frontend captures camera frames at ~10 FPS and sends them over a WebSocket as base64 JPEG. The `media_pipe_service` decodes each frame, runs `mediapipe.solutions.hands` to detect 21 hand landmarks, and crops the hand region (224×224 px) for the classifier.

### Stage 2 — Sign Classification (S3D ONNX)

The hand crops are accumulated in a per-session sliding window of **32 frames**. When the buffer is full, the S3D model runs inference:

- **Model:** `S3D.onnx` from [ai-forever/easy_sign](https://github.com/ai-forever/easy_sign) — auto-downloaded on first startup
- **Input tensor:** `(1, 3, 32, 224, 224)` — batch × RGB channels × frames × height × width
- **Output:** top-1 RSL word from `RSL_class_list.txt` (1,598 classes) + confidence score
- **Threshold:** predictions below `0.5` confidence are discarded

When no hand is detected for ~1.5 seconds ("rest detection"), the accumulated sign sequence is flushed and sent to Stage 3.

### Stage 3 — LLM Translation (Gemini)

The `llm_service` receives the raw sign sequence (e.g. `["привет", "мир", "как"]`) and calls Gemini 2.5 Flash to produce a grammatically correct sentence in the target language (Russian, English, or Kazakh). Session context is stored in Redis so follow-up sentences stay coherent.

---

## Architecture

```
Browser (HTTPS :443)
        │
        ▼
┌───────────────────────────────────────────┐
│          Nginx Gateway (:80 / :443)        │
│  /           → Frontend     (React :8080)  │
│  /ws/        → MediaPipe    (WS    :8001)  │
│  /api/v1/    → LLM Service  (REST  :8002)  │
│  /auth/      → Auth Service (REST  :8003)  │
└──────┬────────────┬───────────┬────────────┘
       │            │           │
       ▼            ▼           ▼
   Frontend     Auth Svc    MediaPipe Svc
   React :8080  FastAPI      FastAPI :8001
                :8003            │
                  │         S3D ONNX model
                MongoDB      (1,598 RSL)
                :27017            │
                             LLM Service
                             FastAPI :8002
                                  │
                           Gemini API + Redis
                                  :6379
```

---

## Project Structure

```
VUR/
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment variable template
├── Makefile                    # Convenience targets (make dev, make build)
│
├── nginx/
│   ├── gateway.conf            # Nginx reverse proxy rules + TLS config
│   └── gen-certs.sh            # Self-signed certificate generator (runs at startup)
│
├── frontend/                   # React 19 + TypeScript (Vite)
│   ├── src/
│   │   ├── App.tsx             # Root component — camera, WebSocket, layout
│   │   ├── components/
│   │   │   ├── Camera.tsx      # Video element + canvas overlay
│   │   │   ├── LandmarkOverlay.tsx  # Draws 21-point hand skeleton on canvas
│   │   │   ├── TranslationPanel.tsx # Detected signs, confidence, history
│   │   │   ├── Controls.tsx    # Start / Stop / Clear buttons
│   │   │   └── StatusBar.tsx   # Frame quality, stability, guidance messages
│   │   ├── hooks/
│   │   │   ├── useCamera.ts    # MediaStream access, frame capture → base64
│   │   │   ├── useWebSocket.ts # WS connection, frame send/receive
│   │   │   ├── useToast.ts     # Auto-dismiss notifications
│   │   │   └── useSpeech.ts    # Text-to-speech output
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── SignupPage.tsx
│   │   │   ├── VerifyEmailPage.tsx
│   │   │   ├── ForgotPasswordPage.tsx
│   │   │   ├── ResetPasswordPage.tsx
│   │   │   └── ProfilePage.tsx
│   │   ├── store/
│   │   │   ├── useAppStore.ts  # Session, detected signs, translation history
│   │   │   └── useAuthStore.ts # User, access/refresh tokens
│   │   └── services/
│   │       ├── api.ts          # LLM & session REST calls
│   │       └── authApi.ts      # Auth endpoints
│   └── Dockerfile
│
├── backend/
│   ├── media_pipe_service/     # Hand detection + S3D classification
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI entry point, Prometheus metrics
│   │   │   ├── config.py       # Settings (thresholds, S3D window size, etc.)
│   │   │   ├── models/
│   │   │   │   ├── s3d_classifier.py    # ONNX Runtime inference, auto-download
│   │   │   │   └── gesture_classifier.py # Per-session frame buffer → S3D call
│   │   │   ├── services/
│   │   │   │   ├── hand_detector.py    # MediaPipe Hands wrapper, crop extraction
│   │   │   │   ├── sign_buffer.py      # Rest detection, sequence debounce
│   │   │   │   └── ws_auth.py          # JWT validation for WebSocket
│   │   │   └── routers/
│   │   │       ├── websocket.py        # WS handler, per-session state, ThreadPool
│   │   │       └── health.py
│   │   ├── scripts/
│   │   │   ├── record_training_data.py
│   │   │   ├── train_classifier.py
│   │   │   └── evaluate_classifier.py
│   │   ├── data/               # Model cache, training data
│   │   └── requirements.txt
│   │
│   ├── llm_service/            # Gemini translation + session management
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI, rate limiting (30 req/min)
│   │   │   ├── config.py       # Gemini model, Redis URL, system prompt
│   │   │   ├── clients/
│   │   │   │   └── gemini_client.py    # google-genai SDK, prompt building
│   │   │   ├── processors/
│   │   │   │   └── sentence_builder.py # Orchestrates translation + session
│   │   │   ├── context/
│   │   │   │   ├── session_manager.py       # In-memory sessions (fallback)
│   │   │   │   └── redis_session_manager.py # Redis-backed sessions
│   │   │   └── routers/
│   │   │       ├── translate.py  # POST /api/v1/translate, session CRUD
│   │   │       └── health.py
│   │   └── requirements.txt
│   │
│   └── auth_service/           # User accounts, JWT, 2FA, email
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py       # JWT secret, token TTLs, SMTP settings
│       │   ├── models/
│       │   │   └── user.py     # MongoDB user document
│       │   ├── routers/
│       │   │   └── auth.py     # All /auth/* endpoints
│       │   ├── services/
│       │   │   ├── token_service.py    # JWT issue / verify (HS256)
│       │   │   ├── password_service.py # bcrypt hashing
│       │   │   ├── email_service.py    # SMTP verification & reset emails
│       │   │   ├── twofa_service.py    # TOTP setup, recovery codes
│       │   │   ├── csrf_service.py     # CSRF token generation / validation
│       │   │   └── session_service.py  # Login session tracking
│       │   └── schemas/
│       │       └── auth.py     # Pydantic request/response models
│       └── requirements.txt
│
└── docs/
    └── evaluation.md
```

---

## Services

### Frontend — React 19 + TypeScript (Vite)

- Live camera feed with **21-point hand skeleton overlay** drawn on a canvas element
- Real-time detected RSL signs with confidence scores
- Automatic translation on hand drop, or manual via button
- Language selector: Russian / English / Kazakh
- Toast notifications for errors, fallback mode, and translation results
- Full auth flow: register, email verification, login, 2FA (TOTP), password reset, profile

### MediaPipe Service — Port 8001

- FastAPI WebSocket server (`/ws/sign-detection?token=JWT`)
- Accepts base64 JPEG frames from the frontend
- MediaPipe Hands: detects 21 landmarks, extracts 224×224 hand crop
- **S3D ONNX model** (ai-forever/easy_sign): classifies RSL gestures from 32-frame temporal windows, 1,598 word classes
- Per-session frame buffer managed in a `deque`; S3D runs in a `ThreadPoolExecutor` to avoid blocking the event loop
- Rest detection: flushes sign sequence to frontend when hand disappears for 1,500 ms
- Sends back: detected sign, confidence, landmarks array, frame quality/stability metrics, guidance text

### LLM Service — Port 8002

- FastAPI REST API (`POST /api/v1/translate`)
- Receives raw sign sequences and context from the frontend
- Builds a structured prompt for **Gemini 2.5 Flash** (temp 0.2, max 128 tokens)
- System prompt specialised for RSL: handles fingerspelling vs. whole-word glosses
- Session history stored in **Redis** (falls back to in-memory if Redis unavailable)
- Rate limited to 30 requests/min per IP
- Graceful degradation: returns space-joined signs if Gemini API is unavailable

### Auth Service — Port 8003

- FastAPI REST API (`/auth/*`)
- JWT authentication — HS256, 15-min access tokens, 7-day refresh tokens
- Email verification on registration (SMTP)
- TOTP two-factor authentication with recovery codes
- Password reset via email tokens (30-min TTL)
- CSRF token protection on state-changing endpoints
- User data stored in **MongoDB**

### Nginx Gateway

- Single entry point on ports 80 (redirects to HTTPS) and 443
- Routes traffic to all four internal services based on path prefix
- WebSocket proxy with long timeouts (3,600 s) for `/ws/`
- Self-signed TLS certificate generated at first Docker startup via `gen-certs.sh`

---

## Quick Start

### Docker (recommended)

```bash
# 1. Copy and fill in secrets
cp .env.example .env
# Required: GEMINI_API_KEY, MONGODB_URL, JWT_SECRET, EMAIL_HOST/PORT/USER/PASSWORD

# 2. Start everything
docker compose up --build

# App is available at https://localhost
# Accept the self-signed TLS certificate warning in your browser
```

### Local Development

```bash
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
cp .env.example .env  # add GEMINI_API_KEY
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# Terminal 4 — Frontend
cd frontend
cp .env.local.example .env.local  # set local service URLs
npm install
npm run dev  # http://localhost:5173
```

Or with Make:

```bash
make dev
```

---

## Environment Variables

Root `.env` (used by Docker Compose):

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `MONGODB_URL` | Yes | MongoDB connection string |
| `MONGODB_DB` | Yes | MongoDB database name (default: `vur`) |
| `JWT_SECRET` | Yes | ≥32 character secret for HS256 signing |
| `EMAIL_HOST` | Yes | SMTP host (e.g. `smtp.gmail.com`) |
| `EMAIL_PORT` | Yes | SMTP port (e.g. `587`) |
| `EMAIL_USER` | Yes | SMTP username |
| `EMAIL_PASSWORD` | Yes | SMTP app password |
| `CORS_ORIGINS` | No | Allowed origins, comma-separated |
| `LOG_LEVEL` | No | Logging level (default: `info`) |

Frontend `.env.local` (local dev only):

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_LLM_URL` | `http://localhost:8002` | LLM service base URL |
| `VITE_AUTH_URL` | `http://localhost:8003` | Auth service base URL |
| `VITE_WS_URL` | `ws://localhost:8001` | MediaPipe WebSocket URL |

---

## WebSocket Protocol

**Connect:** `wss://<host>/ws/sign-detection?token=<JWT>`

**Client → Server (send frame)**
```json
{
  "type": "frame",
  "payload": {
    "image": "<base64 JPEG>",
    "session_id": "<uuid>",
    "timestamp": 1707151200000
  }
}
```

**Server → Client (detection result)**
```json
{
  "type": "detection",
  "payload": {
    "sign": "привет",
    "confidence": 0.95,
    "hand_detected": true,
    "landmarks": [[0.51, 0.72], "..."],
    "guidance": "Keep hand centered",
    "frame_quality": 0.85,
    "stability": 0.78,
    "sequence_length": 3
  }
}
```

When no hand is detected for 1.5 s the server sends `"type": "rest"` to indicate the sign sequence should be flushed to the LLM service.

---

## REST API

**Translate signs to sentence**

```
POST /api/v1/translate
Authorization: Bearer <JWT>

{
  "sign_sequence": ["привет", "мир"],
  "session_id": "<uuid>",
  "context": "optional previous sentence",
  "language": "ru"
}
```

```json
{
  "translation": "Привет, мир!",
  "confidence": 0.92,
  "session_id": "<uuid>",
  "processing_time_ms": 450,
  "fallback": false
}
```

**Auth endpoints** — `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/verify-email`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/2fa/setup`, `/auth/2fa/verify`

**Health checks** — `GET /health` (LLM), `GET /health/mediapipe`, `GET /health` (Auth)

**Metrics** — `GET /metrics` (Prometheus, all services)

---

## ML Model Details

### S3D ONNX — Russian Sign Language

| Property | Value |
|----------|-------|
| Source | [ai-forever/easy_sign](https://github.com/ai-forever/easy_sign) |
| Architecture | S3D (Separable 3D ConvNet) |
| Classes | 1,598 RSL words |
| Input | (1, 3, 32, 224, 224) — batch × RGB × frames × H × W |
| Inference runtime | ONNX Runtime (CPU) |
| Confidence threshold | 0.5 (configurable via `S3D_THRESHOLD`) |
| Download | Auto on first startup, cached in Docker volume |

### MediaPipe Hands

Detects 21 3D landmarks per hand. Each landmark is normalised to [0, 1] relative to the wrist. The service crops the bounding box of the detected hand and resizes it to 224×224 for the S3D model.

Configuration (`media_pipe_service/app/config.py`):
- `MAX_NUM_HANDS`: 1
- `MIN_DETECTION_CONFIDENCE`: 0.5
- `MIN_TRACKING_CONFIDENCE`: 0.5
- `S3D_WINDOW_SIZE`: 32 frames

### Gemini 2.5 Flash

Used for grammar correction and natural language generation from raw sign sequences. Configured with temperature 0.2 for deterministic output. The system prompt instructs the model to act as an RSL expert, handle both fingerspelling and whole-word glosses, and output fluent sentences in the target language.

---

## Evaluation

```bash
# Classifier metrics + confusion matrix
cd backend/media_pipe_service
source venv/bin/activate
python scripts/evaluate_classifier.py --data data/landmarks.csv --out-dir reports

# Translation latency + keyword quality
cd backend/llm_service
source venv/bin/activate
python scripts/benchmark_translation.py \
  --cases evaluation/translation_cases.json \
  --out reports/translation_benchmark.json
```

Generated artifacts:
- `backend/media_pipe_service/reports/classifier_metrics.json`
- `backend/media_pipe_service/reports/confusion_matrix.csv`
- `backend/llm_service/reports/translation_benchmark.json`

See `docs/evaluation.md` for the full evaluation workflow.

---

## How to Use

1. Open `https://localhost` and sign in (register if first time — accept the self-signed cert warning)
2. Allow camera access when prompted
3. Select your target language (Russian / English / Kazakh)
4. Click **Start Translation**
5. Perform RSL hand signs — the skeleton overlay confirms the camera sees your hand
6. Detected signs appear in the panel in real time
7. Translation fires automatically when you lower your hand (rest detection), or click **Translate Signs to Sentence**
8. Click **Clear** to reset the sign buffer and start a new sentence

---

## Project Status

| Component | Status |
|-----------|--------|
| Auth Service | Complete |
| MediaPipe Hand Detection | Complete |
| S3D RSL Classifier (1,598 classes) | Complete — auto-downloaded from GitHub |
| Rest Detection & Sign Buffering | Complete |
| LLM Translation (Gemini 2.5 Flash) | Complete |
| Session Caching (Redis) | Complete |
| Frontend UI | Complete |
| Hand Landmark Overlay | Complete |
| Multi-language Support (RU / EN / KZ) | Complete |
| HTTPS / TLS (self-signed) | in-Complete |
| API Gateway (Nginx) | in-Complete |
| Docker Compose | Complete |
| Prometheus Metrics | in-Complete |
| Evaluation Scripts | in-Complete |

---

## Repository

https://github.com/RakhatLukum646/VUR
