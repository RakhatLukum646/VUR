# SignZhan — MediaPipe Service

Real-time hand landmark detection and sign classification service for SignZhan.

This service accepts camera frames over WebSocket, runs MediaPipe Hands (21 landmarks),
and performs sign classification (S3D ONNX) on 32-frame windows.

For full system architecture and how components fit together, see the root `README.md`.

## Run (local)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## WebSocket

- Endpoint: `ws://localhost:8001/ws/sign-detection`

## Health

- `GET /api/v1/health`
