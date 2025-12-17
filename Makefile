.PHONY: help setup dev test lint clean docker-build docker-up docker-down docker-logs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial project setup
	@echo "Setting up Ans project..."
	@cp -n .env.example .env 2>/dev/null || true
	@echo " Environment file created (.env)"
	@echo " Please edit .env with your configuration"
	@echo "Next: Run 'make docker-build' to build containers"

docker-build: ## Build Docker containers
	@echo "Building Docker containers..."
	docker compose -f infrastructure/docker-compose.dev.yml build

docker-up: ## Start all services
	@echo "Starting Ans development environment..."
	docker compose -f infrastructure/docker-compose.dev.yml up -d
	@echo " Services started"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"

docker-down: ## Stop all services
	@echo "Stopping services..."
	docker compose -f infrastructure/docker-compose.dev.yml down

docker-logs: ## View logs from all services
	docker compose -f infrastructure/docker-compose.dev.yml logs -f

docker-logs-backend: ## View backend logs
	docker compose -f infrastructure/docker-compose.dev.yml logs -f backend

docker-logs-frontend: ## View frontend logs
	docker compose -f infrastructure/docker-compose.dev.yml logs -f frontend

dev: docker-up ## Start development environment (alias for docker-up)

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test

test-backend: ## Run backend tests only
	cd backend && pytest -v

test-frontend: ## Run frontend tests only
	cd frontend && npm test

lint: ## Run linters
	@echo "Linting backend..."
	cd backend && black app/ && ruff app/
	@echo "Linting frontend..."
	cd frontend && npm run lint

clean: ## Clean up containers and volumes
	@echo "Cleaning up..."
	docker compose -f infrastructure/docker-compose.dev.yml down -v
	@echo " Containers and volumes removed"

db-migrate: ## Run database migrations
	docker compose -f infrastructure/docker-compose.dev.yml exec backend alembic upgrade head

db-rollback: ## Rollback last migration
	docker compose -f infrastructure/docker-compose.dev.yml exec backend alembic downgrade -1

db-shell: ## Open PostgreSQL shell
	docker compose -f infrastructure/docker-compose.dev.yml exec postgres psql -U postgres -d ans_dev

redis-shell: ## Open Redis CLI
	docker compose -f infrastructure/docker-compose.dev.yml exec redis redis-cli

backend-shell: ## Open backend container shell
	docker compose -f infrastructure/docker-compose.dev.yml exec backend /bin/bash

status: ## Show status of all services
	docker compose -f infrastructure/docker-compose.dev.yml ps
