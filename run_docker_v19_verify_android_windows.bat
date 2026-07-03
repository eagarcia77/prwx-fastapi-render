@echo off
REM PR-WX v1.9 Verify Services + Android Earthquake Bridge
call docker compose build --no-cache
call docker compose run --rm prwx-update-once
call docker compose up prwx-dashboard
