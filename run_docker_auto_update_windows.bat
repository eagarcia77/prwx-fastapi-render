@echo off
docker compose --profile updater up -d prwx-updater
docker compose logs -f prwx-updater
pause
