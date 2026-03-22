.PHONY: dev test lint migrate

dev:
	docker-compose up --build

test:
	cd apps/api && python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=75 -q

lint:
	cd apps/api && ruff check . && ruff format --check .
	cd apps/api && bandit -r app -ll -q

migrate:
	cd apps/api && alembic upgrade head
