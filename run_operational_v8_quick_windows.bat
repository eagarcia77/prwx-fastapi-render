@echo off
python scripts\19_operational_update_v8.py --limit 12
streamlit run dashboard\app.py
