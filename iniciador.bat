@echo off

cd /d "%~dp0"

call .\venv\Scripts\activate

@echo off
call venv\Scripts\activate

start cmd /k uvicorn webhook_app:app --host 0.0.0.0 --port 8000
start cmd /k python run_worker.py
start cmd /k ngrok http 8000

echo.
echo "EL BOT SE ESTA EJECUTANDO CORRECTAMENTE ruta ", "%~dp0"
pause