@echo off
python scripts
_operational_update_v5.py --limit 12
streamlit run dashboardpp.py
pause
