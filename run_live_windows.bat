@echo off
python scripts\02_build_training_table.py
python scripts\03_train_bias_model.py
python scripts\05_download_nws_live.py
python scripts\06_predict_live_nws.py
streamlit run dashboard\app.py
