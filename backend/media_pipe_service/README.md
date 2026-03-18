# MediaPipe Service - Sign Language Detection

**Developer:** Vlad (Backend - MediaPipe)

Real-time hand gesture detection service using MediaPipe and FastAPI.

## Features

- 🔴 **Real-time hand detection** - 21 landmark tracking at 30+ FPS
- 🎯 **Gesture classification** - ASL alphabet (A-Z) and numbers (0-9)
- 🔄 **WebSocket streaming** - Low-latency frame processing
- 📊 **Sign sequence buffer** - Intelligent sign accumulation
- 🔗 **LLM integration** - Automatic translation requests

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

## WebSocket API

**Endpoint:** `ws://localhost:8001/ws/sign-detection`

### Send Frame
```json
{
  "type": "frame",
  "payload": {
    "image": "base64_jpeg_string",
    "timestamp": 1707151200000,
    "session_id": "uuid"
  }
}
```

### Receive Detection
```json
{
  "type": "detection",
  "payload": {
    "sign": "H",
    "confidence": 0.95,
    "hand_detected": true,
    "timestamp": 1707151200000
  }
}
```

## Project Structure

```
app/
├── main.py              # FastAPI entry
├── config.py            # Settings
├── models/
│   ├── schemas.py       # Pydantic models
│   └── gesture_classifier.py  # Sign classification
├── services/
│   ├── hand_detector.py # MediaPipe integration
│   └── sign_buffer.py   # Sequence management
└── routers/
    ├── websocket.py     # WebSocket endpoint
    └── health.py        # Health checks
```

## Testing

```bash
pytest tests/
```

## Evaluation

```bash
python scripts/evaluate_classifier.py --data data/landmarks.csv --out-dir reports
```

Outputs:
- `reports/classifier_metrics.json`
- `reports/confusion_matrix.csv`
- `reports/predictions.csv`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8001 | Service port |
| CONFIDENCE_THRESHOLD | 0.7 | Min detection confidence |
| LLM_SERVICE_URL | http://localhost:8002 | LLM service endpoint |
