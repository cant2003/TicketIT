from bot.services.usuarios_service import es_ti_por_telegram_id


def es_ti(chat_id):
    return es_ti_por_telegram_id(chat_id)