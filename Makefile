.PHONY: dev test lint migrate format install help

API_DIR = apps/api

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install API dependencies
	cd $(API_DIR) && pip install -e ".[dev]"

dev:  ## Start development services
	docker compose up --build

dev-down:  ## Stop development services
	docker compose down

test:  ## Run tests with coverage
	cd $(API_DIR) && python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80

test-ci:  ## Run tests in CI (docker)
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from api_test

lint:  ## Run linting (ruff + bandit)
	cd $(API_DIR) && ruff check .
	cd $(API_DIR) && ruff format --check .
	cd $(API_DIR) && bandit -r app/ -c pyproject.toml

format:  ## Auto-format code
	cd $(API_DIR) && ruff check --fix .
	cd $(API_DIR) && ruff format .

migrate:  ## Run alembic migrations
	cd $(API_DIR) && alembic upgrade head

migrate-new:  ## Create a new migration (usage: make migrate-new MSG="description")
	cd $(API_DIR) && alembic revision --autogenerate -m "$(MSG)"

migrate-down:  ## Rollback last migration
	cd $(API_DIR) && alembic downgrade -1

logs:  ## Tail API logs
	docker compose logs -f api
