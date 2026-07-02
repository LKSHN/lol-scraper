#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose up -d db

echo "Waiting for Postgres to be ready..."
until docker compose exec -T db pg_isready -U lol_scraper > /dev/null 2>&1; do
  sleep 1
done

uv run alembic upgrade head
echo "Postgres is up and migrations are applied."
