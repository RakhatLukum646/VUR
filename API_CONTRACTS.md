# API Contracts - Sign Language Translator

## Overview
This document defines all API contracts between services.

---

## 1. WebSocket API (Frontend ↔ MediaPipe)

### Endpoint
```
ws://localhost:8001/ws/sign-detection
```

### Messages

#### Client → Server: Send Video Frame
```json
{
  "type": "frame",
  "payload": {
    "image": "base64_encoded_jpeg_string",
    "timestamp": 1707151200000,
    "session_id": "uuid-v4-string"
  }
}
```

#### Server → Client: Detection Result
```json
{
  "type": "detection",
  "payload": {
    "sign": "H",
    "confidence": 0.95,
    "hand_detected": true,
    "landmarks": [[x1, y1], [x2, y2], ...],
    "timestamp": 1707151200000
  }
}
```

#### Server → Client: No Hand Detected
```json
{
  "type": "detection",
  "payload": {
    "sign": null,
    "confidence": 0,
    "hand_detected": false,
    "timestamp": 1707151200000
  }
}
```

#### Client → Server: Start/Stop Session
```json
// Start
{
  "type": "command",
  "payload": {
    "action": "start",
    "session_id": "uuid-v4-string"
  }
}

// Stop
{
  "type": "command",
  "payload": {
    "action": "stop",
    "session_id": "uuid-v4-string"
  }
}
```

---

## 2. REST API (MediaPipe ↔ LLM Service)

### Translate Sign Sequence

**Endpoint:** `POST http://localhost:8002/api/v1/translate`

**Request:**
```json
{
  "sign_sequence": ["H", "E", "L", "L", "O"],
  "session_id": "uuid-v4-string",
  "context": "previous conversation context",
  "language": "en"
}
```

**Response (200 OK):**
```json
{
  "translation": "Hello, how are you?",
  "confidence": 0.92,
  "session_id": "uuid-v4-string",
  "processing_time_ms": 450,
  "alternatives": ["Hello there!", "Hello everyone!"]
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Invalid sign sequence",
  "message": "Sign sequence cannot be empty"
}
```

### Get Session Context

**Endpoint:** `GET http://localhost:8002/api/v1/context/{session_id}`

**Response:**
```json
{
  "session_id": "uuid-v4-string",
  "context": "Hello, how are you?",
  "history": [
    {"signs": ["H", "E", "L", "L", "O"], "translation": "Hello"},
    {"signs": ["H", "O", "W", "A", "R", "E", "Y", "O", "U"], "translation": "how are you"}
  ]
}
```

### Clear Session

**Endpoint:** `DELETE http://localhost:8002/api/v1/context/{session_id}`

**Response:**
```json
{
  "message": "Session cleared successfully",
  "session_id": "uuid-v4-string"
}
```

---

## 3. REST API (Frontend ↔ API Gateway)

### Health Check

**Endpoint:** `GET http://localhost:8000/api/v1/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "api_gateway": "up",
    "media_pipe": "up",
    "llm": "up"
  },
  "version": "1.0.0"
}
```

### Batch Translate (For recorded videos)

**Endpoint:** `POST http://localhost:8000/api/v1/batch-translate`

**Request:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "language": "en",
  "options": {
    "frame_rate": 30,
    "confidence_threshold": 0.8
  }
}
```

**Response:**
```json
{
  "job_id": "uuid-v4-string",
  "status": "processing",
  "estimated_time_ms": 5000
}
```

### Get Batch Job Status

**Endpoint:** `GET http://localhost:8000/api/v1/batch-translate/{job_id}`

**Response:**
```json
{
  "job_id": "uuid-v4-string",
  "status": "completed",
  "result": {
    "translation": "Hello, nice to meet you",
    "signs_detected": ["H", "E", "L", "L", "O", "N", "I", "C", "E", "T", "O", "M", "E", "E", "T", "Y", "O", "U"],
    "confidence": 0.89
  }
}
```

---

## 4. Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `CAMERA_ERROR` | Cannot access camera | 400 |
| `NO_HAND_DETECTED` | No hand visible in frame | 200 (with empty result) |
| `INVALID_SIGN` | Unrecognized sign gesture | 200 (with low confidence) |
| `LLM_TIMEOUT` | Gemini API timeout | 504 |
| `LLM_RATE_LIMIT` | Gemini rate limit exceeded | 429 |
| `INVALID_SESSION` | Session not found | 404 |
| `SERVICE_UNAVAILABLE` | Backend service down | 503 |

---

## 5. Data Types

### TypeScript Interfaces (Frontend)

```typescript
// Detection Result from WebSocket
interface DetectionResult {
  type: 'detection';
  payload: {
    sign: string | null;
    confidence: number;
    hand_detected: boolean;
    landmarks?: [number, number][];
    timestamp: number;
  };
}

// Translation Response
interface TranslationResponse {
  translation: string;
  confidence: number;
  session_id: string;
  processing_time_ms: number;
  alternatives?: string[];
}

// Health Check Response
interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services: {
    api_gateway: 'up' | 'down';
    media_pipe: 'up' | 'down';
    llm: 'up' | 'down';
  };
  version: string;
}
```

### Pydantic Models (Python Backend)

```python
# Shared models for all Python services
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SignSequence(BaseModel):
    signs: List[str]
    session_id: str
    timestamp: datetime = datetime.utcnow()

class TranslationRequest(BaseModel):
    sign_sequence: List[str]
    session_id: str
    context: Optional[str] = None
    language: str = "en"

class TranslationResponse(BaseModel):
    translation: str
    confidence: float
    session_id: str
    processing_time_ms: int
    alternatives: Optional[List[str]] = None

class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    services: dict
    version: str
```
