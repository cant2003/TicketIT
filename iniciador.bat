@echo off

cd /d "%~dp0"

call .\venv\Scripts\activate

start cmd /k python -m bot.bot

start cmd /k python run_worker.py 

echo.
echo "EL BOT SE ESTA EJECUTANDO CORRECTAMENTE ruta ", "%~dp0"
pause