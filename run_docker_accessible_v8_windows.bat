@echo off
docker compose build --no-cache
docker compose run --rm prwx-update-once
docker compose up prwx-dashboard
