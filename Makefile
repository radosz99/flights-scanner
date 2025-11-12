.PHONY: help backend backend-dev frontend install-backend install-frontend test test-api test-all docker-build docker-up docker-down docker-dev-up docker-dev-down docker-logs docker-backend-logs docker-restart docker-rebuild docker-rebuild-backend docker-clean-build docker-deploy clean

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "  Local development:"
	@echo "    make install-backend     - Install backend dependencies"
	@echo "    make install-frontend    - Install frontend dependencies"
	@echo "    make backend             - Run backend API server (port 8900)"
	@echo "    make backend-dev         - Run backend with hot reload connecting to Docker MongoDB"
	@echo "    make frontend            - Run frontend dev server (port 8901)"
	@echo "    make test                - Run all backend tests"
	@echo "    make test-api            - Run API service tests only"
	@echo "    make test-all            - Run all tests with coverage report"
	@echo ""
	@echo "  Docker commands (Production):"
	@echo "    make docker-build            - Build all Docker images"
	@echo "    make docker-up               - Start all services with Docker Compose (production mode)"
	@echo "    make docker-down             - Stop all services"
	@echo "    make docker-deploy           - Complete deployment: build, start, and restart all services"
	@echo "    make docker-rebuild          - Stop, rebuild ALL images (no cache), and start"
	@echo "    make docker-rebuild-backend  - Stop, rebuild BACKEND only (no cache), and start"
	@echo "    make docker-clean-build      - Clean rebuild of ALL services (removes volumes)"
	@echo "    make docker-logs             - Show logs from all services"
	@echo "    make docker-backend-logs     - Show backend logs (last 100 lines, follow)"
	@echo "    make docker-restart          - Restart all services (without rebuilding)"
	@echo ""
	@echo "  Docker commands (Development):"
	@echo "    make docker-dev-up       - Start all services in development mode with hot reload"
	@echo "    make docker-dev-down     - Stop development services"
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

backend-dev:
	@echo "Starting backend in development mode with hot reload..."
	@echo "Connecting to MongoDB at mongodb://localhost:8902"
	@echo ""
	@echo "Make sure MongoDB container is running with: docker-compose up -d mongodb"
	@echo ""
	cd backend && \
	MONGO_HOST=localhost MONGO_PORT=8902 \
	uvicorn api.api:app --host 0.0.0.0 --port 8900 --reload

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
	docker-compose --profile production build

docker-up:
	docker-compose --profile production up -d
	@echo ""
	@echo "Services starting in PRODUCTION mode:"
	@echo "  - Backend API: http://localhost:8900"
	@echo "  - Frontend:    http://localhost:8901"
	@echo "  - MongoDB:     mongodb://localhost:8902"
	@echo "  - Nginx:       http://localhost:80 (HTTPS: 443)"
	@echo ""
	@echo "Run 'make docker-logs' to see logs"

docker-down:
	docker-compose --profile production down

docker-logs:
	docker-compose --profile production logs -f

docker-backend-logs:
	docker-compose --profile production logs -f --tail 100 backend

docker-restart:
	docker-compose --profile production restart

docker-deploy:
	@echo "Starting complete deployment..."
	@echo "Step 1/3: Building all images..."
	docker-compose --profile production build
	@echo ""
	@echo "Step 2/3: Starting all services..."
	docker-compose --profile production up -d
	@echo ""
	@echo "Step 3/3: Restarting all services to ensure proper initialization..."
	docker-compose --profile production restart
	@echo ""
	@echo "✓ Deployment complete!"
	@echo ""
	@echo "Services running in PRODUCTION mode:"
	@echo "  - Backend API: http://localhost:8900"
	@echo "  - Frontend:    http://localhost:8901"
	@echo "  - MongoDB:     mongodb://localhost:8902"
	@echo "  - Nginx:       http://localhost:80 (HTTPS: 443)"
	@echo ""
	@echo "Run 'make docker-logs' to see logs"

docker-rebuild:
	@echo "Stopping all services..."
	docker-compose --profile production down
	@echo "Rebuilding all images (no cache)..."
	docker-compose --profile production build --no-cache
	@echo "Starting services..."
	docker-compose --profile production up -d
	@echo ""
	@echo "✓ All services rebuilt and started"
	@echo "Run 'make docker-logs' to see logs"

docker-rebuild-backend:
	@echo "Stopping backend service..."
	docker-compose --profile production stop backend
	@echo "Rebuilding backend image (no cache)..."
	docker-compose --profile production build --no-cache backend
	@echo "Starting backend service..."
	docker-compose --profile production up -d backend
	@echo ""
	@echo "✓ Backend rebuilt and started"
	@echo "Run 'make docker-backend-logs' to see logs"

docker-clean-build:
	@echo "WARNING: This will remove all containers, images, and volumes!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	docker-compose --profile production down -v
	docker-compose --profile production build --no-cache
	docker-compose --profile production up -d
	@echo ""
	@echo "✓ Clean rebuild complete (volumes removed)"
	@echo "Run 'make docker-logs' to see logs"

# Docker development commands
docker-dev-up:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
	@echo ""
	@echo "Services starting in DEVELOPMENT mode with hot reload:"
	@echo "  - Backend API: http://localhost:8900 (with hot reload)"
	@echo "  - Frontend:    http://localhost:8901 (with hot reload)"
	@echo "  - MongoDB:     mongodb://localhost:8902"
	@echo ""
	@echo "Mobile/Network Access:"
	@echo "  Access from other devices on the same network using your local IP:"
	@LOCAL_IP=$$(ip route get 1 2>/dev/null | grep -oP 'src \K\S+' || ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $$2}' | head -1 || echo "Unable to detect IP"); \
	echo "  - Frontend:    http://$$LOCAL_IP:8901"; \
	echo "  - Backend API: http://$$LOCAL_IP:8900"
	@echo ""
	@echo "Code changes will automatically reload the services."
	@echo "Run 'docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f' to see logs"

docker-dev-down:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Utility commands
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf .nuxt node_modules/.cache 2>/dev/null || true
