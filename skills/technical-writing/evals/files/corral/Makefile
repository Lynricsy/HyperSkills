.PHONY: test lint typecheck

test:
	uv run pytest -q

lint:
	uv run ruff check src tests

typecheck:
	uv run mypy src
