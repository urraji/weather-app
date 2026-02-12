.PHONY: run test lint fmt docker-build

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-graceful-shutdown 25

test:
	pytest -q

lint:
	python -m compileall app/ -q

fmt:
	python -m pip install -q ruff
	ruff format app tests

docker-build:
	docker build -t weather-alert-service:latest .
