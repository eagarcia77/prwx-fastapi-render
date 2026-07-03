@echo off
uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
pause
