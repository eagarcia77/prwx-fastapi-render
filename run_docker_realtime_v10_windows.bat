@echo off
echo Iniciando PR-WX v1.0 con temperatura, lluvia, viento y alertas...
docker compose build
docker compose run --rm prwx-update-once
docker compose up prwx-dashboard
