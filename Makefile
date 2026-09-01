.PHONY: setup dev demo test test-backend build-frontend docker clean

setup:
	./scripts/setup.sh

dev:
	./scripts/dev.sh

demo:
	./.venv/bin/python sample_data/generate_demo.py
	./.venv/bin/python scripts/seed_demo.py --run --wait

test: test-backend build-frontend

test-backend:
	cd backend && ../.venv/bin/python -m pytest -q

build-frontend:
	cd frontend && npx tsc --noEmit && npm run build

docker:
	docker compose up --build

clean:
	rm -rf backend/storage/*.db backend/storage/users frontend/.next
