# ! configuiracion de tokens y ID
import os
from pathlib import Path

from dotenv import load_dotenv

directorio_actual = Path(__file__).resolve().parent
ruta_env = directorio_actual.parent / ".env"

load_dotenv(dotenv_path=ruta_env)

TOKEN = os.getenv("TELEGRAM_TOKEN")

USUARIOS_TI = [
    os.getenv("CRISTIAN_ID"),
    # os.getenv("USUARIO_2"),
]

EMAIL_PASS = os.getenv("EMAIL_PASS")
REMITENTE = os.getenv("REMITENTE")
DESTINATARIO = os.getenv("DESTINATARIO")

GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Tickets")

WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))