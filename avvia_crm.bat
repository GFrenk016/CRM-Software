@echo off
title CRM La Piacentino
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Primo avvio: preparazione in corso, un momento...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

start "" http://localhost:5000
python app.py

pause