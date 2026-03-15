# Setup Guide - Sign Language Translator

## Quick Start

### Option 1: Docker (Recommended for demo)
```bash
docker-compose up
```

### Option 2: Local Development
```bash
# Terminal 1: MediaPipe Service
cd backend/media_pipe_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Terminal 2: LLM Service
cd backend/llm_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Add GEMINI_API_KEY to .env
uvicorn main:app --reload --port 8002

# Terminal 3: API Gateway
cd backend/api_gateway
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 4: Frontend
cd frontend
npm install
npm run dev
```

---

## Prerequisites

### Required Software
- **Node.js** 18+ → [Download](https://nodejs.org/)
- **Python** 3.10+ → [Download](https://python.org/)
- **Git** → [Download](https://git-scm.com/)

### Optional (Recommended)
- **Docker Desktop** → [Download](https://www.docker.com/products/docker-desktop)
- **VS Code** → [Download](https://code.visualstudio.com/)

---

## Detailed Setup

### 1. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

### 2. Clone Repository

```bash
git clone <your-repo-url>
cd sign-language-translator
```

### 3. Environment Setup

Create `.env` files in each service directory:

#### `backend/llm_service/.env`
```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-pro
PORT=8002
```

#### `backend/media_pipe_service/.env`
```
PORT=8001
CONFIDENCE_THRESHOLD=0.7
```

#### `backend/api_gateway/.env`
```
PORT=8000
MEDIAPIPE_URL=http://localhost:8001
LLM_URL=http://localhost:8002
```

### 4. Frontend Setup (Ulzhan)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:5173
```

### 5. Backend Setup (Vlad & Rakhat)

#### MediaPipe Service (Vlad)

```bash
cd backend/media_pipe_service

# Create virtual environment
python -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn main:app --reload --port 8001
```

#### LLM Service (Rakhat)

```bash
cd backend/llm_service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Run service
uvicorn main:app --reload --port 8002
```

---

## Project Structure After Setup

```
sign-language-translator/
├── frontend/                    # React app
│   ├── node_modules/            # Dependencies
│   ├── src/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── media_pipe_service/      # Vlad's service
│   │   ├── venv/                # Python environment
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── .env
│   │
│   ├── llm_service/             # Rakhat's service
│   │   ├── venv/                # Python environment
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── .env
│   │
│   └── api_gateway/
│       ├── venv/
│       ├── main.py
│       └── requirements.txt
│
└── docker-compose.yml
```

---

## Common Commands

### Frontend (Ulzhan)
```bash
cd frontend

npm run dev          # Start dev server
npm run build        # Build for production
npm run lint         # Check code style
npm run preview      # Preview production build
```

### Backend (Vlad & Rakhat)
```bash
# In each service directory

source venv/bin/activate    # Activate environment
uvicorn main:app --reload   # Start with auto-reload
uvicorn main:app --port 8000 # Start on specific port

# Deactivate when done
deactivate
```

---

## Troubleshooting

### Frontend Issues

**Error: `npm install` fails**
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Error: Camera not working**
- Use `http://localhost:5173` (not `127.0.0.1`)
- Check browser camera permissions
- Ensure you're on HTTPS or localhost

### Backend Issues

**Error: `ModuleNotFoundError`**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Error: `Address already in use`**
```bash
# Find and kill process using port
lsof -ti:8001 | xargs kill -9  # Mac/Linux
# or use different port
uvicorn main:app --reload --port 8003
```

**Error: Gemini API fails**
- Check `.env` file exists with valid `GEMINI_API_KEY`
- Verify API key hasn't expired
- Check internet connection

---

## Development URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React app |
| API Gateway | http://localhost:8000 | Main API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MediaPipe | http://localhost:8001 | Hand detection |
| LLM Service | http://localhost:8002 | Gemini integration |

---

## Next Steps

1. **Verify setup**: All services should start without errors
2. **Test camera**: Open frontend and allow camera access
3. **Test detection**: Make hand gestures in front of camera
4. **Check integration**: Signs should appear as text in the UI
