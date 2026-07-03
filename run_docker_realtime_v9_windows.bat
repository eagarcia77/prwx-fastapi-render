@echo off
echo Construyendo y ejecutando PR-WX v0.9 con Docker...
docker compose build
docker compose run --rm prwx-update-once
docker compose up prwx-dashboard
