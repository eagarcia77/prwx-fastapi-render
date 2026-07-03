@echo off
setlocal
docker compose build
docker compose run --rm prwx-update-once
docker compose up prwx-dashboard
