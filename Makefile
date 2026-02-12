run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-graceful-shutdown 25

test:
	pytest -q

docker-build:
	docker build -t weather-api:latest .
