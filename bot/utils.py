from bot.config import USUARIOS_TI

#! Verificacion TI
def es_ti(chat_id):
    return str(chat_id) in USUARIOS_TI