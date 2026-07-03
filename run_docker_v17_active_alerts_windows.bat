@echo off
REM PR-WX v1.7 Active Alerts Hardened
call docker compose build --no-cache
call docker compose run --rm prwx-update-once
call docker compose up prwx-dashboard
