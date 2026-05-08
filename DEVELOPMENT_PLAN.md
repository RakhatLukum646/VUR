# SignZhan — Development Plan (AI sign language recognition)

## 📋 Project Overview

**Topic:** SignZhan — AI-powered sign language recognition for real-time translation
**Team:** 3 Developers
- **Ulzhan** - Frontend Developer (React)
- **Vlad** - Backend Developer (Python, MediaPipe)
- **Rakhat** - Backend Developer (Python, Gemini LLM)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Camera     │  │  Video      │  │  Translated Text        │  │
│  │  Component  │  │  Preview    │  │  Display                │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘  │
│         │                                                        │
│         ▼ WebSocket / HTTP                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (Python/FastAPI)                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  MediaPipe Service (Vlad)                               │    │
│  │  - Hand landmark detection                              │    │
│  │  - Gesture classification                               │    │
│  │  - Sign sequence extraction                             │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  LLM Service (Rakhat)                                   │    │
│  │  - Gemini API integration                               │    │
│  │  - Sign → Natural language conversion                   │    │
│  │  - Context management                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
sign-language-translator/
├── 📁 frontend/                    # Ulzhan's workspace
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Camera/            # Webcam capture component
│   │   │   ├── VideoPreview/      # Live video with landmarks
│   │   │   ├── TranslationPanel/  # Display translated text
│   │   │   └── Controls/          # Start/Stop/Settings
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts    # WebSocket connection hook
│   │   │   └── useCamera.ts       # Camera access hook
│   │   ├── services/
│   │   │   └── api.ts             # API client
│   │   ├── types/
│   │   │   └── index.ts           # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── 📁 backend/                     # Shared backend workspace
│   ├── 📁 media_pipe_service/      # Vlad's workspace
│   │   ├── models/
│   │   │   └── gesture_classifier.py
│   │   ├── processors/
│   │   │   └── hand_processor.py
│   │   ├── utils/
│   │   │   └── landmarks.py
│   │   ├── requirements.txt
│   │   └── main.py
│   │
│   ├── 📁 llm_service/             # Rakhat's workspace
│   │   ├── clients/
│   │   │   └── gemini_client.py
│   │   ├── processors/
│   │   │   └── sentence_builder.py
│   │   ├── context/
│   │   │   └── session_manager.py
│   │   ├── requirements.txt
│   │   └── main.py
│   │
│   ├── 📁 api_gateway/             # Shared: API routing
│   │   ├── routers/
│   │   │   ├── translation.py
│   │   │   └── websocket.py
│   │   ├── middleware/
│   │   ├── requirements.txt
│   │   └── main.py                 # FastAPI entry point
│   │
│   └── 📁 shared/                  # Shared utilities
│       ├── models/
│       │   └── schemas.py          # Pydantic models
│       └── utils/
│           └── config.py
│
├── 📁 docker/                      # Docker configurations
│   ├── docker-compose.yml
│   ├── frontend.Dockerfile
│   └── backend.Dockerfile
│
├── 📁 docs/                        # Documentation
│   ├── API.md
│   └── SETUP.md
│
└── Makefile                        # Easy local build commands
```

---

## 🛠️ Tech Stack

### Frontend (Ulzhan)
| Component | Technology |
|-----------|------------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite |
| UI Library | Tailwind CSS + shadcn/ui |
| State Management | Zustand |
| WebSocket | Native WebSocket API |
| Camera Access | MediaDevices API |

### Backend - MediaPipe Service (Vlad)
| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Framework | FastAPI |
| Hand Detection | MediaPipe Hands |
| Gesture Classification | Custom classifier / MediaPipe Gesture |
| Communication | WebSocket for real-time |

### Backend - LLM Service (Rakhat)
| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Framework | FastAPI |
| LLM | Google Gemini API |
| Context Management | In-memory / Redis (optional) |
| Communication | HTTP/REST |

### DevOps / Shared
| Component | Technology |
|-----------|------------|
| Containerization | Docker + Docker Compose |
| Process Manager | Concurrently (npm) |
| Environment | python-dotenv |

---

## 👥 Task Breakdown

### 🔷 Ulzhan (Frontend) - Week 1-2

#### Week 1: Setup & Camera
- [ ] Initialize React project with Vite + TypeScript
- [ ] Setup Tailwind CSS and shadcn/ui
- [ ] Create Camera component with MediaDevices API
- [ ] Implement video preview with recording indicator
- [ ] Add error handling for camera permissions

#### Week 2: UI & WebSocket
- [ ] Design main layout (video left, translation right)
- [ ] Create TranslationPanel component
- [ ] Implement WebSocket connection hook
- [ ] Add controls (Start/Stop translation, Clear text)
- [ ] Create loading/error states

**Deliverables:**
- Working camera capture
- WebSocket client ready
- UI components complete

---

### 🔶 Vlad (MediaPipe) - Week 1-2

#### Week 1: Setup & Hand Detection
- [ ] Setup Python virtual environment
- [ ] Install MediaPipe, OpenCV, FastAPI
- [ ] Create hand landmark detection module
- [ ] Extract 21 hand landmarks per frame
- [ ] Build landmark normalization (relative coordinates)

#### Week 2: Gesture Classification
- [ ] Create gesture classifier (start with basic signs: A-Z, 0-9)
- [ ] Build sign sequence buffer (collect multiple frames)
- [ ] Implement gesture-to-letter mapping
- [ ] Create WebSocket endpoint for real-time streaming
- [ ] Add confidence threshold filtering

**Deliverables:**
- MediaPipe service running locally
- WebSocket endpoint accepting video frames
- Returns detected signs as text stream

---

### 🔶 Rakhat (LLM Service) - Week 1-2

#### Week 1: Setup & Gemini Integration
- [ ] Setup Python virtual environment
- [ ] Create Gemini API client
- [ ] Implement prompt engineering for sign language
- [ ] Build basic sentence generation from sign sequences
- [ ] Add API endpoint for text translation

#### Week 2: Context & Polish
- [ ] Implement session-based context management
- [ ] Add grammar correction and natural language processing
- [ ] Create fallback for unrecognized signs
- [ ] Build health check endpoints
- [ ] Add request/response logging

**Deliverables:**
- LLM service running locally
- REST API accepting sign sequences
- Returns natural language sentences

---

## 🔌 API Contracts

### WebSocket: Frontend ↔ MediaPipe Service

```javascript
// Connection
ws://localhost:8001/ws/sign-detection

// Client → Server (send frame)
{
  "frame": "base64_encoded_image",  // JPEG frame from camera
  "timestamp": 1707151200
}

// Server → Client (detected sign)
{
  "sign": "H",                      // Detected sign letter/gesture
  "confidence": 0.95,
  "timestamp": 1707151200,
  "hand_detected": true
}
```

### HTTP: MediaPipe Service ↔ LLM Service

```python
# POST /api/v1/translate
Request:
{
    "sign_sequence": ["H", "E", "L", "L", "O"],
    "session_id": "uuid-123",
    "context": "previous sentence context"  # optional
}

Response:
{
    "translation": "Hello, how are you?",
    "confidence": 0.92,
    "session_id": "uuid-123",
    "suggestions": ["Hello there!", "Hello everyone!"]  # optional
}
```

### HTTP: Frontend ↔ API Gateway

```typescript
// POST /api/v1/translate (batch mode, optional)
Request:
{
    "video_url": "uploaded_video_url"  // for recorded video translation
}

// GET /api/v1/health
Response:
{
    "status": "healthy",
    "services": {
        "media_pipe": "up",
        "llm": "up"
    }
}
```

---

## 🚀 Local Development Setup

### Prerequisites
- Node.js 18+
- Python 3.10+
- Docker (optional but recommended)
- Google Gemini API Key

### Quick Start (One Command)

```bash
# Clone and enter project
git clone <repo-url>
cd sign-language-translator

# Start everything with Docker (Recommended)
docker-compose up

# Or start locally with Make
make dev
```

### Manual Setup

#### 1. Backend Setup (Vlad & Rakhat)

```bash
# In separate terminals

# Terminal 1: MediaPipe Service (Vlad)
cd backend/media_pipe_service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Terminal 2: LLM Service (Rakhat)
cd backend/llm_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env file with GEMINI_API_KEY
uvicorn main:app --reload --port 8002

# Terminal 3: API Gateway (Shared)
cd backend/api_gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### 2. Frontend Setup (Ulzhan)

```bash
cd frontend
npm install
npm run dev
```

### Access Points
- **Frontend:** http://localhost:5173
- **API Gateway:** http://localhost:8000
- **MediaPipe Service:** http://localhost:8001
- **LLM Service:** http://localhost:8002

---

## 🔀 Development Workflow

### Branch Strategy

```
main (production-ready)
  ├── develop (integration branch)
  │     ├── feature/ulzhan-camera-component
  │     ├── feature/vlad-mediapipe-detection
  │     └── feature/rakhat-gemini-integration
```

### Git Workflow

```bash
# Each developer works on their feature branch
git checkout -b feature/ulzhan-camera-component

# Regular commits
git add .
git commit -m "feat: add camera component with permission handling"

# Push and create PR to develop branch
git push origin feature/ulzhan-camera-component
# Create Pull Request on GitHub
```

### Communication Protocol

1. **Daily Standups** (5 min): Share blockers and progress
2. **API Contract First**: Agree on interfaces before implementation
3. **Integration Day**: Mid-week sync to test integration
4. **End-of-Week Demo**: Show working features

---

## 📦 Dependencies

### Frontend package.json
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.4.0",
    "tailwindcss": "^3.4.0",
    "lucide-react": "^0.300.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

### Backend requirements.txt (MediaPipe)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
mediapipe==0.10.9
opencv-python==4.9.0.80
numpy==1.26.3
websockets==12.0
python-multipart==0.0.6
pydantic==2.5.0
```

### Backend requirements.txt (LLM)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
google-generativeai==0.3.2
python-dotenv==1.0.0
httpx==0.26.0
pydantic==2.5.0
redis==5.0.1  # optional for context
```

---

## 🎯 Milestones

### Week 1: Foundation
- [ ] All developers have local environment running
- [ ] Ulzhan: Camera working, can capture video
- [ ] Vlad: MediaPipe detecting hand landmarks
- [ ] Rakhat: Gemini API responding to requests

### Week 2: Integration
- [ ] Frontend ↔ MediaPipe connected via WebSocket
- [ ] MediaPipe ↔ LLM connected via HTTP
- [ ] End-to-end: Sign → Detected Letters → Natural Sentence
- [ ] Basic UI showing real-time translation

### Week 3: Polish (Optional)
- [ ] Improve gesture accuracy
- [ ] Better context management
- [ ] UI/UX refinements
- [ ] Error handling and edge cases

---

## 🔧 Troubleshooting

### Common Issues

1. **Camera not accessible**
   - Check browser permissions
   - Ensure HTTPS or localhost (required for camera)

2. **MediaPipe not detecting hands**
   - Ensure good lighting
   - Check camera resolution (min 640x480)

3. **Gemini API errors**
   - Verify API key in .env
   - Check API rate limits

4. **WebSocket connection fails**
   - Verify all services are running
   - Check CORS settings

---

## 📚 Resources

### MediaPipe
- [MediaPipe Hands](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)
- [Python Setup Guide](https://developers.google.com/mediapipe/solutions/setup_python)

### Gemini API
- [Gemini API Docs](https://ai.google.dev/docs)
- [Python Quickstart](https://ai.google.dev/tutorials/python_quickstart)

### React + WebSocket
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [React useWebSocket Hook](https://github.com/robtaussig/react-use-websocket)

---

## ✅ Success Criteria

- [ ] User can open web app, allow camera, and see video
- [ ] When user makes sign language gestures, hand landmarks appear
- [ ] Detected signs stream in real-time
- [ ] Natural language translation appears after sign sequence
- [ ] Project builds and runs with single command (`make dev` or `docker-compose up`)

---

*Plan created for the SignZhan team*
*Last updated: 2026-02-08*
