@echo off
REM PR-WX Hybrid Model v0.4 - local auto updater
REM Default: update every 30 minutes. Change INTERVAL_SECONDS if needed.
set INTERVAL_SECONDS=1800
:loop
echo.
echo ==========================================================
echo Updating PR-WX live forecast at %date% %time%
echo ==========================================================
python scripts\07_update_live_pipeline.py --all --append-history
if errorlevel 1 echo Update failed. Check the console output above.
timeout /t %INTERVAL_SECONDS% /nobreak
goto loop
