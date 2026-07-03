@echo off
REM PR-WX v1.8 MRMS Fix + Life Safety
call docker compose build --no-cache
call docker compose run --rm prwx-update-once
call docker compose up prwx-dashboard
