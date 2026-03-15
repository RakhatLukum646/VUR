# Sign Language Translator - Makefile
# Easy commands to build and run the project

.PHONY: help install dev build clean docker-up docker-down

# Default target
help:
	@echo "Sign Language Translator - Available Commands"
	@echo ""
	@echo "  make install     - Install all dependencies"
	@echo "  make dev         - Start all services in development mode"
	@echo "  make build       - Build production images"
	@echo "  make docker-up   - Start with Docker Compose"
	@echo "  make docker-down - Stop Docker Compose"
	@echo "  make clean       - Clean up temporary files"
	@echo "  make test        - Run tests"
	@echo ""

# Install dependencies for all services
install:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	
	@echo "Installing MediaPipe service dependencies..."
	cd backend/media_pipe_service && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	
	@echo "Installing LLM service dependencies..."
	cd backend/llm_service && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	
	@echo "Installing API Gateway dependencies..."
	cd backend/api_gateway && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	
	@echo "Done! Create .env files and run 'make dev'"

# Start all services (requires tmux or multiple terminals)
dev:
	@echo "Starting all services..."
	@echo "Frontend: http://localhost:5173"
	@echo "API Gateway: http://localhost:8000"
	@echo "MediaPipe: http://localhost:8001"
	@echo "LLM Service: http://localhost:8002"
	@echo ""
	@echo "Run these commands in separate terminals:"
	@echo ""
	@echo "Terminal 1 (Frontend):"
	@echo "  cd frontend && npm run dev"
	@echo ""
	@echo "Terminal 2 (MediaPipe):"
	@echo "  cd backend/media_pipe_service && source venv/bin/activate && uvicorn main:app --reload --port 8001"
	@echo ""
	@echo "Terminal 3 (LLM):"
	@echo "  cd backend/llm_service && source venv/bin/activate && uvicorn main:app --reload --port 8002"
	@echo ""
	@echo "Terminal 4 (API Gateway):"
	@echo "  cd backend/api_gateway && source venv/bin/activate && uvicorn main:app --reload --port 8000"

# Build for production
build:
	@echo "Building frontend..."
	cd frontend && npm run build
	
	@echo "Building Docker images..."
	docker-compose build

# Docker commands
docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

docker-clean:
	docker-compose down -v
	docker system prune -f

# Clean temporary files
clean:
	@echo "Cleaning up..."
	cd frontend && rm -rf node_modules dist
	cd backend/media_pipe_service && rm -rf venv __pycache__ .pytest_cache
	cd backend/llm_service && rm -rf venv __pycache__ .pytest_cache
	cd backend/api_gateway && rm -rf venv __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Done!"

# Run tests
test:
	@echo "Running frontend tests..."
	cd frontend && npm test
	
	@echo "Running backend tests..."
	cd backend/media_pipe_service && source venv/bin/activate && pytest
	cd backend/llm_service && source venv/bin/activate && pytest
	cd backend/api_gateway && source venv/bin/activate && pytest

# Quick health check
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/api/v1/health | python -m json.tool || echo "API Gateway not running"
