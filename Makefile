.PHONY: help build build-cpp build-python test test-unit test-integration test-load clean setup install run run-api run-db format lint type-check docker-build docker-up docker-down docs coverage benchmark

# Variables
PYTHON := python3
PIP := pip3
VENV := venv
PROJECT_NAME := gen-db
API_PORT := 8000
DB_PORT := 5432

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)$(PROJECT_NAME) - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Examples:$(NC)"
	@echo "  make setup          # Complete initial setup"
	@echo "  make run            # Start API and database"
	@echo "  make test           # Run all tests"
	@echo "  make build          # Build everything"

## ============================================================================
## SETUP & INITIALIZATION
## ============================================================================

setup: setup-python setup-cpp ## Complete setup (Python + C++)
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo "Next steps:"
	@echo "  1. Export environment: source $(VENV)/bin/activate"
	@echo "  2. Start API: make run"

setup-python: ## Setup Python virtual environment
	@echo "$(BLUE)Setting up Python environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip setuptools wheel
	. $(VENV)/bin/activate && cd src/backend && pip install -r requirements.txt
	@echo "$(GREEN)✓ Python setup complete$(NC)"

setup-cpp: ## Build C++ components
	@echo "$(BLUE)Building C++ components...$(NC)"
	@if [ ! -d "csubgraph-main/build" ]; then \
		mkdir -p csubgraph-main/build; \
	fi
	cd csubgraph-main/build && \
	cmake .. -DCMAKE_BUILD_TYPE=Release && \
	cmake --build . --config Release -j4
	@echo "$(GREEN)✓ C++ build complete$(NC)"

## ============================================================================
## BUILD
## ============================================================================

build: build-cpp build-python ## Build all components

build-cpp: ## Build C++ subgraph-cli
	@echo "$(BLUE)Building C++ component...$(NC)"
	cd csubgraph-main/build && cmake --build . --config Release -j4
	@echo "$(GREEN)✓ C++ build complete: csubgraph-main/build/subgraph-cli$(NC)"

build-python: ## Install Python dependencies
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	. $(VENV)/bin/activate && cd src/backend && pip install -r requirements.txt
	@echo "$(GREEN)✓ Python dependencies installed$(NC)"

## ============================================================================
## TESTING
## ============================================================================

test: test-unit test-integration ## Run all tests

test-unit: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	. $(VENV)/bin/activate && pytest tests/test_subgraph_executor.py -v --tb=short

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	. $(VENV)/bin/activate && pytest tests/test_integration.py -v --tb=short

test-app: ## Run app tests
	@echo "$(BLUE)Running app tests...$(NC)"
	. $(VENV)/bin/activate && pytest tests/test_app.py -v --tb=short

test-load: ## Run load tests
	@echo "$(BLUE)Running load tests...$(NC)"
	@echo "Make sure API is running: make run-api"
	. $(VENV)/bin/activate && python load_test.py --concurrent 4 --creates 20 --searches 30

coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	. $(VENV)/bin/activate && pytest tests/ --cov=src/backend --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report: htmlcov/index.html$(NC)"

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	. $(VENV)/bin/activate && python load_test.py --concurrent 8 --creates 50 --searches 100

## ============================================================================
## DEVELOPMENT
## ============================================================================

run: run-db run-api ## Start API and database

run-api: ## Start API server (development)
	@echo "$(BLUE)Starting API server...$(NC)"
	. $(VENV)/bin/activate && cd src/backend && \
	python -m uvicorn app:app --reload --host 0.0.0.0 --port $(API_PORT)

run-db: ## Start PostgreSQL database (Docker)
	@echo "$(BLUE)Starting PostgreSQL database...$(NC)"
	@if ! docker ps | grep -q gendb-postgres; then \
		docker run -d \
			--name gendb-postgres \
			-e POSTGRES_PASSWORD=postgres \
			-p $(DB_PORT):5432 \
			postgres:15-alpine; \
		echo "$(GREEN)Database started$(NC)"; \
	else \
		echo "$(YELLOW)Database already running$(NC)"; \
	fi

stop-db: ## Stop PostgreSQL database
	@echo "$(BLUE)Stopping PostgreSQL database...$(NC)"
	docker stop gendb-postgres || true
	docker rm gendb-postgres || true

format: ## Format code (Black + isort)
	@echo "$(BLUE)Formatting Python code...$(NC)"
	. $(VENV)/bin/activate && pip install black isort
	. $(VENV)/bin/activate && black src/backend tests/
	. $(VENV)/bin/activate && isort src/backend tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Lint code (flake8)
	@echo "$(BLUE)Linting code...$(NC)"
	. $(VENV)/bin/activate && pip install flake8
	. $(VENV)/bin/activate && flake8 src/backend tests/ --max-line-length=127
	@echo "$(GREEN)✓ Linting complete$(NC)"

type-check: ## Type checking with mypy
	@echo "$(BLUE)Type checking...$(NC)"
	. $(VENV)/bin/activate && pip install mypy
	. $(VENV)/bin/activate && mypy src/backend --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking complete$(NC)"

format-cpp: ## Format C++ code (clang-format)
	@echo "$(BLUE)Formatting C++ code...$(NC)"
	find csubgraph-main -name "*.cpp" -o -name "*.h" | xargs clang-format -i
	@echo "$(GREEN)✓ C++ code formatted$(NC)"

## ============================================================================
## DOCKER
## ============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t gen-db:latest gen-db-main/
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-up: ## Start full stack with Docker Compose
	@echo "$(BLUE)Starting Docker stack...$(NC)"
	cd gen-db-main && docker-compose up -d
	@echo "$(GREEN)✓ Stack running on http://localhost:8000$(NC)"

docker-down: ## Stop Docker stack
	@echo "$(BLUE)Stopping Docker stack...$(NC)"
	cd gen-db-main && docker-compose down
	@echo "$(GREEN)✓ Stack stopped$(NC)"

docker-logs: ## Show Docker logs
	cd gen-db-main && docker-compose logs -f api

docker-clean: docker-down ## Clean Docker resources
	@echo "$(BLUE)Cleaning Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓ Cleaned$(NC)"

## ============================================================================
## DOCUMENTATION
## ============================================================================

docs: ## Generate API documentation
	@echo "$(BLUE)API docs available at:$(NC)"
	@echo "  Swagger: http://localhost:$(API_PORT)/docs"
	@echo "  ReDoc:   http://localhost:$(API_PORT)/redoc"

docs-open: ## Open API documentation in browser
	@echo "$(BLUE)Opening API documentation...$(NC)"
	@command -v open >/dev/null 2>&1 && open http://localhost:$(API_PORT)/docs || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:$(API_PORT)/docs || \
	echo "Please open http://localhost:$(API_PORT)/docs manually"

coverage-open: ## Open coverage report
	@echo "$(BLUE)Opening coverage report...$(NC)"
	@command -v open >/dev/null 2>&1 && open htmlcov/index.html || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open htmlcov/index.html || \
	echo "Please open htmlcov/index.html manually"

## ============================================================================
## MAINTENANCE
## ============================================================================

clean: clean-python clean-cpp clean-docker ## Clean all build artifacts

clean-python: ## Clean Python artifacts
	@echo "$(BLUE)Cleaning Python artifacts...$(NC)"
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-cpp: ## Clean C++ build artifacts
	@echo "$(BLUE)Cleaning C++ artifacts...$(NC)"
	rm -rf csubgraph-main/build
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-docker: ## Clean Docker containers and images
	@echo "$(BLUE)Cleaning Docker...$(NC)"
	docker stop gendb-postgres 2>/dev/null || true
	docker rm gendb-postgres 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

install: ## Install all dependencies
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	. $(VENV)/bin/activate && pip install --upgrade pip
	. $(VENV)/bin/activate && cd src/backend && pip install -r requirements.txt
	. $(VENV)/bin/activate && pip install pytest pytest-asyncio pytest-cov aiohttp flake8 mypy black isort
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

requirements: ## Generate requirements.txt
	@echo "$(BLUE)Generating requirements...$(NC)"
	. $(VENV)/bin/activate && pip freeze > requirements-all.txt
	@echo "$(GREEN)✓ Generated: requirements-all.txt$(NC)"

## ============================================================================
## DATABASE
## ============================================================================

db-init: ## Initialize database
	@echo "$(BLUE)Initializing database...$(NC)"
	@if command -v psql >/dev/null 2>&1; then \
		psql -U postgres -h localhost -d gendb < init_db.sql; \
	else \
		docker-compose exec postgres psql -U postgres -d gendb < init_db.sql; \
	fi
	@echo "$(GREEN)✓ Database initialized$(NC)"

db-reset: ## Reset database (warning: deletes all data!)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d postgres; \
		sleep 3; \
		make db-init; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
	else \
		echo "Cancelled"; \
	fi

db-shell: ## Open database shell
	@echo "$(BLUE)Opening database shell...$(NC)"
	@if docker ps | grep -q gendb-postgres; then \
		docker-compose exec postgres psql -U postgres -d gendb; \
	else \
		psql -U postgres -h localhost -d gendb; \
	fi

## ============================================================================
## DEPLOYMENT
## ============================================================================

deploy-local: docker-build docker-up db-init ## Deploy locally with Docker
	@echo "$(GREEN)✓ Deployed locally!$(NC)"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

deploy-k8s: ## Deploy to Kubernetes
	@echo "$(BLUE)Deploying to Kubernetes...$(NC)"
	kubectl apply -f gen-db-main/k8s/deployment.yaml
	@echo "$(GREEN)✓ Deployed to Kubernetes$(NC)"

## ============================================================================
## UTILITY
## ============================================================================

env-setup: ## Setup environment variables
	@echo "$(BLUE)Setting up environment...$(NC)"
	@if [ ! -f ".env" ]; then \
		cp gen-db-main/.env.template .env; \
		echo "$(GREEN)✓ Created .env from template$(NC)"; \
		echo "$(YELLOW)⚠ Edit .env with your settings$(NC)"; \
	else \
		echo "$(YELLOW).env already exists$(NC)"; \
	fi

version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "CMake: $$(cmake --version | head -1)"
	@if command -v docker >/dev/null 2>&1; then \
		echo "Docker: $$(docker --version)"; \
	fi

info: ## Show project information
	@echo "$(BLUE)$(PROJECT_NAME) - Project Information$(NC)"
	@echo "API Port: $(API_PORT)"
	@echo "DB Port: $(DB_PORT)"
	@echo "Venv: $(VENV)"
	@echo ""
	@echo "$(BLUE)Quick Links:$(NC)"
	@echo "  Setup:     make setup"
	@echo "  Run:       make run"
	@echo "  Test:      make test"
	@echo "  Docs:      make docs-open"

## ============================================================================
## DEFAULT
## ============================================================================

.DEFAULT_GOAL := help
