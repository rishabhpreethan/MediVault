.PHONY: up down logs shell-api shell-worker migrate test lint

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell-api:
	docker compose exec api bash

shell-worker:
	docker compose exec worker bash

migrate:
	docker compose exec api alembic upgrade head

migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

test-backend:
	docker compose -f docker-compose.test.yml up -d
	docker compose -f docker-compose.test.yml exec api-test pytest
	docker compose -f docker-compose.test.yml down

test-frontend:
	cd frontend && npm run test

lint-backend:
	cd backend && ruff check . && mypy app/

lint-frontend:
	cd frontend && npm run lint && npm run typecheck

setup:
	cp -n .env.example .env || true
	docker compose build
	docker compose up -d
	sleep 5
	docker compose exec api alembic upgrade head
	@echo "MediVault is running at http://localhost:5173"
