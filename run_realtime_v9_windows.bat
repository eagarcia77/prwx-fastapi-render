@echo off
echo Iniciando PR-WX v0.9 Realtime Accessible Command Center...
python scripts\20_operational_update_v9.py
streamlit run dashboard\app.py
