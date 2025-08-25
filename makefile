.PHONY: test up down rebuild clean

test:
	@PYTHONPATH=. TESTING=1 pytest -q

up:
	@docker compose -f docker-compose.dev.yaml up --build

down:
	@docker compose -f docker-compose.dev.yaml down

rebuild:
	@docker compose -f docker-compose.dev.yaml up -d --build

clean:
	@docker compose -f docker-compose.dev.yaml down -v
	@rm -rf __pycache__ .pytest_cache .ruff_cache
