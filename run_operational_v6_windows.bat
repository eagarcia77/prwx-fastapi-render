@echo off
setlocal
python scripts\15_operational_update_v6.py
streamlit run dashboard\app.py
