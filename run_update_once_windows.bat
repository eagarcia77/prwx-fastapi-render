@echo off
REM PR-WX Hybrid Model v0.4 - one live update
python scripts\07_update_live_pipeline.py --all --append-history --fail-on-empty
pause
