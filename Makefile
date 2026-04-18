.PHONY: api web test lint seed smoke format demo

api:
	cd apps/api && uv run uvicorn src.main:app --reload --port 8000

web:
	cd apps/web && pnpm dev

test:
	cd apps/api && uv run pytest tests/ -m "not slow" -q

lint:
	cd apps/api && uv run ruff check . && uv run ruff format --check .
	cd apps/web && pnpm lint

format:
	cd apps/api && uv run ruff check --fix . && uv run ruff format .

seed:
	cd apps/api && uv run python -m src.scripts.seed_chroma

smoke:
	cd apps/api && uv run python -m src.scripts.smoke_test

demo:
	cd apps/api && uv run python -m src.scripts.run_all_personas
