.PHONY: install install-dev migrate test run validate-launch ci

install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install --upgrade pip
	python -m pip install -r requirements-dev.txt

migrate:
	python -m alembic upgrade head

test:
	python -m pytest -q

run:
	uvicorn app.main:app --reload

validate-launch:
	python scripts/validate_launch_config.py

ci: install-dev validate-launch migrate test
