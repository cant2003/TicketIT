import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from telegram import Update

from bot.bot import build_application

WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

application = build_application()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await application.initialize()
    await application.start()
    yield
    await application.stop()
    await application.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret token")

    data = await request.json()
    update = Update.de_json(data=data, bot=application.bot)
    await application.process_update(update)

    return {"ok": True}

@app.get("/")
async def root():
    return {"message": "Webhook server activo"}

@app.get("/health")
async def health():
    return {"status": "ok"}