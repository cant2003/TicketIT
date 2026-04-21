@echo off
cd /d "%~dp0"

call .\venv\Scripts\activate

start "Webhook" cmd /k uvicorn webhook_app:app --host 0.0.0.0 --port 8000
start "Worker" cmd /k python run_worker.py
start "Ngrok" cmd /k ngrok http 8000

echo.
echo EL BOT SE ESTA EJECUTANDO CORRECTAMENTE
echo Ruta: %~dp0
pause