@echo off

cd /d "%~dp0"

call .\venv\Scripts\activate

pip install -r requirements.txt

python -m bot.bot

echo.
echo "EL BOT SE ESTA EJECUTANDO CORRECTAMENTE ruta ", "%~dp0"
pause