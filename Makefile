install:
	uv sync

dev:
	uv run fast dev

worker:
	uv run fast worker

lint:
	uv run fast lint

format:
	uv run fast format

test:
	uv run fast test

migrate:
	uv run fast db migrate

revision:
	uv run fast db revision
