# Operations Notes

## Runtime Services

- `mongo`: persists auth users, sessions, and password-reset tokens.
- `redis`: backs the LLM sentence builder session cache when enabled.
- `auth-service`: exposes `/health` and configures MongoDB indexes at startup.
- `llm-service`: exposes `/health` and `/api/v1/health`.
- `media-pipe`: exposes `/api/v1/health` and `/api/v1/ready`.

## Request Tracing

All three backend services now attach an `X-Request-ID` response header.

- If the client sends `X-Request-ID`, the services reuse it.
- If no request ID is present, the service generates one.
- Request completion and failure logs include the service name, method, path, status code, duration, and request ID.

## Local Setup

1. Copy the repository root `.env.example` file to `.env`.
2. Fill in the Gemini and email credentials.
3. Start the full stack with `docker-compose up --build`.

For service-only local development, use the service-specific `.env.example` files under each backend directory.

## CI

GitHub Actions runs:

- frontend `npm ci`, `npm run lint`, `npm run build`, and `npm run test -- --run`
- backend `pytest tests/ -v` for `auth_service`, `llm_service`, and `media_pipe_service`
- `python -m compileall app` for `auth_service`
