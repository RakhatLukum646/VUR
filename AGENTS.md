# Repository Guidelines

## Project Structure & Module Organization
`frontend/` contains the React 19 + TypeScript client. UI code lives in `frontend/src`, split across `components/`, `pages/`, `hooks/`, `services/`, `store/`, and `types/`. Static assets live in `frontend/public/`.

`backend/` contains three FastAPI services: `media_pipe_service/`, `llm_service/`, and `auth_service/`. Each service keeps application code under `app/`; only the MediaPipe and LLM services currently include `tests/`. Shared deployment files live in `docker-compose.yml`, `Makefile`, and `nginx/`.

## Virtual Environments
Each backend service has its own isolated `venv/` inside its directory. Global Python has no project packages installed.

Create / recreate a service venv:
```bash
cd backend/<service>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Build, Test, and Development Commands
- `cd frontend && npm install`: install frontend dependencies.
- `cd frontend && npm run dev`: start the Vite client on port `5173`.
- `cd frontend && npm run build`: type-check and build the frontend bundle.
- `cd frontend && npm run lint`: run ESLint for TypeScript and React hooks rules.
- `cd backend/media_pipe_service && source venv/bin/activate && uvicorn app.main:app --reload --port 8001`: run the MediaPipe service.
- `cd backend/llm_service && source venv/bin/activate && uvicorn app.main:app --reload --port 8002`: run the LLM service.
- `cd backend/auth_service && source venv/bin/activate && uvicorn app.main:app --reload --port 8003`: run the auth service.
- `cd backend/<service> && source venv/bin/activate && pytest tests/ -v`: run that service's test suite.
- `docker-compose up --build`: start the nginx gateway plus all services.
Some `Makefile` targets still mention a removed `backend/api_gateway`; prefer the direct commands above.

## Coding Style & Naming Conventions
Use 2-space indentation in `*.ts` and `*.tsx`, and 4 spaces in Python. Prefer functional React components, PascalCase component files such as `TranslationPanel.tsx`, camelCase hooks such as `useWebSocket.ts`, and snake_case Python modules such as `gesture_classifier.py`. Run `npm run lint` before opening a PR.

## Testing Guidelines
Backend tests use `pytest`; name files `test_*.py` and keep them under each service, for example `backend/llm_service/tests/test_session_manager.py`. Run tests per service with `pytest tests/`. There is no frontend test runner configured yet, and `auth_service` currently has no test suite, so include manual verification notes in the PR.

## Commit & Pull Request Guidelines
Recent history mixes short imperative subjects with Conventional Commit prefixes, for example `feat: implement 6 MVP improvements for diploma project`. Prefer `feat:`, `fix:`, or `docs:` with a concise scope. PRs should include a short summary, affected services, linked issues if available, setup or env changes, and screenshots for frontend work.

## Security & Configuration Tips
Do not commit populated `.env` files or API keys. Start from `.env.example` at the repo root and service-specific examples such as `backend/llm_service/.env.example`. Treat generated folders like `venv/`, `dist/`, and `__pycache__/` as local artifacts only.

## Code Standards
- Never typecast. Never use `as`
