.PHONY: dev test lint format migrate clean

dev:
	docker compose up

test:
	cd apps/api && python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=75 -q

test-docker:
	docker compose -f docker-compose.test.yml up --abort-on-container-exit

lint:
	cd apps/api && ruff check . && ruff format --check .

format:
	cd apps/api && ruff check --fix . && ruff format .

migrate:
	docker compose exec api alembic upgrade head

clean:
	docker compose down -v
	find . -type d -name __pycache__ | xargs rm -rf
	find . -type f -name "*.pyc" -delete
