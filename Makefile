install-backend:
	python -m pip install -r backend/requirements.txt

seed:
	python scripts/seed_database.py

test:
	pytest

run-backend:
	uvicorn backend.app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev
