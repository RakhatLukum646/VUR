
## Summary

Strong diploma-quality project with excellent documentation and clean architecture.
The main gaps are: shallow test coverage, missing TLS, no auth on WebSocket, and
in-memory session leaks. Addressing the P0/P1 items below would bring this to
production-ready quality.

---

## P0 — Security (Fix before any public deployment)

### 1. Enable HTTPS at the gateway
**File:** `nginx/gateway.conf`
- Add TLS termination with Let's Encrypt or self-signed cert for local dev
- Set `Secure` flag on all cookies (currently `SameSite=lax` but no `Secure`)
- Redirect HTTP → HTTPS

### 2. Authenticate WebSocket connections
**File:** `backend/media_pipe_service/app/routers/detection.py`
- Extract JWT from `Authorization` header or query param on WebSocket handshake
- Reject unauthenticated connections with `4401` close code
- Reference: auth_service `verify_access_token` dependency already exists

### 3. Rate-limit `/register` endpoint
**File:** `backend/auth_service/app/routers/auth.py`
- Apply the same `slowapi` limiter already used on `/login`
- Suggested limit: 5 registrations/hour per IP
- Add test in `backend/auth_service/tests/test_auth.py`

### 4. Implement refresh token rotation
**File:** `backend/auth_service/app/services/session_service.py`
- On every `/auth/refresh` call: invalidate old token, issue new one
- Store token hash in MongoDB with `used_at` timestamp
- Reject any previously-used refresh token (replay attack protection)

---

## P1 — Reliability

### 5. Add TTL to in-memory session cache
**File:** `backend/llm_service/app/context/session_manager.py`
- Sessions currently accumulate forever in the dict fallback
- Add `last_accessed` timestamp; prune sessions older than 30 minutes
- Or enforce Redis as required dep (remove in-memory fallback entirely)

### 6. Add resource limits to Docker Compose
**File:** `docker-compose.yml`
- MediaPipe is CPU-heavy (OpenCV + MediaPipe per frame)
- Add `deploy.resources.limits` for `media-pipe` (e.g., `cpus: "1.5"`, `memory: 1G`)
- Prevents it from starving `auth-service` and `llm-service`

### 7. Explicit ML model load failure handling
**File:** `backend/media_pipe_service/app/models/gesture_classifier.py`
- Log a clear `WARNING` when model file not found (currently silent)
- Expose a `model_loaded: bool` field in the `/health` response
- Update `backend/media_pipe_service/tests/test_health.py` to assert this field

---

## P2 — Test Coverage

### 8. Replace MongoDB mocks with real integration tests
**File:** `backend/auth_service/tests/test_auth.py`
- Use `mongomock` or spin a real MongoDB in CI via Docker service
- Add tests for: duplicate email constraint, invalid ObjectId, index violations
- Add to `.github/workflows/ci.yml`: `services: mongo: image: mongo:7`

### 9. Add WebSocket integration test for MediaPipe
**File:** `backend/media_pipe_service/tests/` (new file: `test_websocket.py`)
- Use `httpx`+`anyio` or `starlette.testclient.TestClient` WebSocket support
- Send a real base64 JPEG frame; assert landmarks returned
- Test graceful handling of malformed/empty frame

### 10. Frontend: Add critical path tests
**Files:** `frontend/src/test/`
- `useWebSocket.test.ts` — connection, reconnect, message parsing
- `App.integration.test.tsx` — full flow: camera → detection → translation panel
- `authStore.test.ts` — token refresh, logout state cleanup

---

## P3 — Architecture

### 11. Decouple MediaPipe → LLM with a queue
**Files:** `backend/llm_service/app/routers/translate.py`, `docker-compose.yml`
- Currently: MediaPipe calls LLM synchronously over HTTP
- Risk: LLM latency (Gemini API) blocks gesture UI response
- Option A: Redis pub/sub (Redis already in stack) — low complexity
- Option B: Accept async and return translation via WebSocket push

### 12. Add Docker build step to CI
**File:** `.github/workflows/ci.yml`
- Add a job: `docker compose build --no-cache`
- Catches: missing deps in Dockerfile, wrong base images, broken COPY paths
- Run after unit tests pass

### 13. Add pytest coverage threshold
**File:** `.github/workflows/ci.yml` + each service's `pytest.ini` or `pyproject.toml`
- Add `--cov --cov-fail-under=70` to each pytest run
- Forces coverage to not regress as new features are added

---

## P4 — Nice to Have

### 14. Structured metrics endpoint
**Files:** All three `backend/*/app/main.py`
- Expose `/metrics` in Prometheus format (use `prometheus-fastapi-instrumentator`)
- Track: request count, latency p50/p99, WebSocket active connections, Gemini errors

### 15. API versioning consistency
**Files:** `backend/auth_service/app/routers/auth.py`
- Auth routes are `/auth/*` but LLM/MediaPipe use `/api/v1/*`
- Standardize to `/api/v1/auth/*` for consistency
- Update `nginx/gateway.conf` accordingly

### 16. Frontend error boundary
**File:** `frontend/src/App.tsx`
- Wrap camera/translation section in React Error Boundary
- Prevents a WebSocket crash from unmounting the entire app
- Add `frontend/src/components/ErrorBoundary.tsx`

---

## Effort Estimate by Priority

| Priority | Items | Effort |
|----------|-------|--------|
| P0 | #1–4 | ~2–3 days |
| P1 | #5–7 | ~1 day |
| P2 | #8–10 | ~2 days |
| P3 | #11–13 | ~1–2 days |
| P4 | #14–16 | ~2 days |

Total to reach **9/10**: ~8–10 focused dev days.

---

## What's Already Good (Don't Change)

- Microservice separation with Nginx gateway — clean and correct
- Pydantic schemas at all API boundaries — prevents runtime type errors
- TOTP-based 2FA with recovery codes — production-grade auth
- Sign buffer debounce + hand-drop detection — smart UX engineering
- Wrist-relative landmark normalization — good ML preprocessing
- Comprehensive API_CONTRACTS.md + docs/ — rare and valuable
- Docker Compose health checks with dependency ordering — correct
- Structured logging with X-Request-ID tracing — solid observability foundation
