# ! configuiracion de tokens y ID de telegram
import os
from dotenv import load_dotenv
from pathlib import Path

directorio_actual = Path(__file__).resolve().parent
ruta_env = directorio_actual.parent / '.env'

load_dotenv(dotenv_path=ruta_env)

TOKEN = os.getenv("TELEGRAM_TOKEN")

USUARIOS_TI = [
    # os.getenv("CRISTIAN_ID"),
]