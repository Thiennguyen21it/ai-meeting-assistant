### Requirements

- Docker.
- uv for Python package and environment management.

### How to run

- docker compose -f docker-compose-dev.yml watch
- uv sync
- cp .env.example .env
- Change .env environment(openai api key)
- source .venv/bin/activate
- alembic upgrade head
- fastapi dev app/main.py

### How to commit a migration

- alembic revision --autogenerate -m "Commit message"


