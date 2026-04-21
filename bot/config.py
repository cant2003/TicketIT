import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


def _get_env_list(*names):
    return [
        value
        for name in names
        if (value := os.getenv(name))
    ]


# Telegram
TOKEN = os.getenv("TELEGRAM_TOKEN")

USUARIOS_TI = _get_env_list(
    "CRISTIAN_ID",
    "USUARIO_2",
)

# Email
EMAIL_PASS = os.getenv("EMAIL_PASS")
REMITENTE = os.getenv("REMITENTE")
DESTINATARIO = os.getenv("DESTINATARIO")

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Tickets")

# Webhook
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))