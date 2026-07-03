@echo off
python scripts\18_operational_update_v7.py --limit 12
streamlit run dashboard\app.py
