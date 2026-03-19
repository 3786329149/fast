PYTHON ?= python

install:
	$(PYTHON) -m pip install -e .[dev]

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO

lint:
	ruff check app

format:
	black app
	isort app

test:
	pytest -q

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "init"
