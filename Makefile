PYTHON := python
UVICORN := uvicorn

.PHONY: run dev docker-up

run:
	$(UVICORN) backend.app.main:app --host 0.0.0.0 --port 8000

dev:
	$(UVICORN) backend.app.main:app --reload

docker-up:
	docker compose up --build

