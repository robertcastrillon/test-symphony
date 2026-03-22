.PHONY: dev test lint migrate

dev:
	docker-compose up --build

test:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

lint:
	cd apps/api && ruff check . && bandit -r app/ -ll

migrate:
	docker-compose exec api alembic upgrade head
