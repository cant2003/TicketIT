@echo off
cd /d %~dp0
python -m pip install -r requirements.txt
..\venv\Scripts\python.exe app.py
pause
