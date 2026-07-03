@echo off
setlocal
python scripts\15_operational_update_v6.py --limit 12
streamlit run dashboard\app.py
