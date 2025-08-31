@echo off
setlocal
cd /d %~dp0
python -m streamlit run app/ui_streamlit.py
endlocal
