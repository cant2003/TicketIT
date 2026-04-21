import asyncio
import os

from telegram import Bot
from telegram.constants import UpdateType

from bot.config import TOKEN

WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")


async def main():
    if not WEBHOOK_BASE_URL:
        raise ValueError("Falta WEBHOOK_BASE_URL en .env")

    url = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

    bot = Bot(token=TOKEN)

    await bot.set_webhook(
        url=url,
        secret_token=TELEGRAM_WEBHOOK_SECRET or None,
        allowed_updates=[
            UpdateType.MESSAGE,
            UpdateType.CALLBACK_QUERY,
        ],
        max_connections=20,
    )

    info = await bot.get_webhook_info()
    print("Webhook configurado:")
    print(info)


if __name__ == "__main__":
    asyncio.run(main())