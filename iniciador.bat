@echo off
cd /d "%~dp0"


call .\venv\Scripts\activate

python launcher.py

@REM start "Webhook" cmd /k uvicorn webhook_app:app --host 0.0.0.0 --port 8000
@REM start "Worker" cmd /k python run_worker.py
@REM start "Ngrok" cmd /k ngrok http 8000

@REM echo.
@REM echo EL BOT SE ESTA EJECUTANDO CORRECTAMENTE
@REM echo Ruta: %~dp0
pause

