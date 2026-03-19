install:
	uv sync

dev:
	uv run python -m app.cli dev

worker:
	uv run python -m app.cli worker

lint:
	uv run python -m app.cli lint

format:
	uv run python -m app.cli format

test:
	uv run python -m app.cli test

migrate:
	uv run python -m app.cli migrate

revision:
	uv run python -m app.cli revision
