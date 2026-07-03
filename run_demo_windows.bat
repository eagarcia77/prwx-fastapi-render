@echo off
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
python scripts\02_build_training_table.py
python scripts\03_train_bias_model.py
python scripts\04_predict_sample.py
streamlit run dashboard\app.py
