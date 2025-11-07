.PHONY: help backend frontend install-backend install-frontend test test-api test-all docker-build docker-up docker-down docker-logs docker-backend-logs docker-restart clean

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "  Local development:"
	@echo "    make install-backend     - Install backend dependencies"
	@echo "    make install-frontend    - Install frontend dependencies"
	@echo "    make backend             - Run backend API server (port 8900)"
	@echo "    make frontend            - Run frontend dev server (port 8901)"
	@echo "    make test                - Run all backend tests"
	@echo "    make test-api            - Run API service tests only"
	@echo "    make test-all            - Run all tests with coverage report"
	@echo ""
	@echo "  Docker commands:"
	@echo "    make docker-build        - Build all Docker images"
	@echo "    make docker-up           - Start all services with Docker Compose"
	@echo "    make docker-down         - Stop all services"
	@echo "    make docker-logs         - Show logs from all services"
	@echo "    make docker-backend-logs - Show backend logs (last 100 lines, follow)"
	@echo "    make docker-restart      - Restart all services"
	@echo ""
	@echo "  Utility:"
	@echo "    make clean               - Clean up temporary files and caches"
	@echo "    make help                - Show this help message"

# Local development commands
install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

backend:
	cd backend && uvicorn api.api:app --host 0.0.0.0 --port 8900 --reload

frontend:
	cd frontend && npm run dev -- --port 8901

test:
	@echo "Running all backend tests..."
	@echo "NOTE: Tests require MongoDB to be running (see README for setup)"
	cd backend && python -m pytest test_*.py -v

test-api:
	@echo "Running API service integration tests..."
	@echo "NOTE: Tests require MongoDB to be running (see README for setup)"
	cd backend/api && python -m pytest test_api_service.py -v

test-all:
	@echo "Running all tests with coverage..."
	@echo "NOTE: Tests require MongoDB to be running (see README for setup)"
	cd backend && python -m pytest test_*.py -v --cov=. --cov-report=term-missing

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo ""
	@echo "Services starting:"
	@echo "  - Backend API: http://localhost:8900"
	@echo "  - Frontend:    http://localhost:8901"
	@echo "  - MongoDB:     mongodb://localhost:8902"
	@echo ""
	@echo "Run 'make docker-logs' to see logs"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-backend-logs:
	docker-compose logs -f --tail 100 backend

docker-restart:
	docker-compose restart

# Utility commands
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf .nuxt node_modules/.cache 2>/dev/null || true
