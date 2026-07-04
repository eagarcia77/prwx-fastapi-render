@echo off
cd /d %~dp0
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
python scripts\render_bootstrap_v21.py
python scripts\verify_web_mobile_v23.py
pause
