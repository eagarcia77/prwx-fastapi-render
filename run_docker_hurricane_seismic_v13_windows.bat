@echo off
REM PR-WX v1.3 Hurricane + Global Seismic
call docker compose build --no-cache
call docker compose run --rm prwx-update-once
call docker compose up prwx-dashboard
