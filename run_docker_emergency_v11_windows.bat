@echo off
REM PR-WX v1.1 Emergency Display
call docker compose build --no-cache
call docker compose run --rm prwx-update-once
call docker compose up prwx-dashboard
