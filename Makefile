.PHONY: dev log

dev:
	docker compose up -d --build

log:
	docker compose logs -f backend
