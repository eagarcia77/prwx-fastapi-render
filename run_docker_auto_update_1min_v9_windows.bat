@echo off
echo Activando actualizador automatico cada 1 minuto...
docker compose --profile updater up -d prwx-updater
echo Actualizador activo. Para ver logs use: docker compose logs -f prwx-updater
