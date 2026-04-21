from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import TOKEN
from bot.constants.states import (
    AREA,
    DESCRIPCION,
    ESPERANDO_ASIGNADO,
    ESPERANDO_USUARIO,
    ESTADO_ID,
    OBSERVACION,
    RANGO_FIN,
    RANGO_INICIO,
)
from bot.handlers.common import botones, cancelar_global, start
from bot.handlers.report_handlers import (
    recibir_fin,
    recibir_inicio,
    reporte_asignado,
    reporte_usuario,
)
from bot.handlers.ti_handlers import recibir_observacion
from bot.handlers.user_handlers import (
    recibir_area,
    recibir_descripcion,
    ver_estado,
)

TEXT_INPUT = filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$")

def _text_handler(callback):
    return MessageHandler(TEXT_INPUT, callback)

def _build_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(botones)],
        states={
            AREA: [_text_handler(recibir_area)],
            DESCRIPCION: [_text_handler(recibir_descripcion)],
            ESTADO_ID: [_text_handler(ver_estado)],
            OBSERVACION: [_text_handler(recibir_observacion)],
            ESPERANDO_ASIGNADO: [_text_handler(reporte_asignado)],
            ESPERANDO_USUARIO: [_text_handler(reporte_usuario)],
            RANGO_INICIO: [_text_handler(recibir_inicio)],
            RANGO_FIN: [_text_handler(recibir_fin)],
        },
        fallbacks=[
            MessageHandler(filters.Regex("(?i)^cancelar$"), cancelar_global),
            CommandHandler("cancelar", cancelar_global),
        ],
    )

def build_application() -> Application:
    application = Application.builder().token(TOKEN).updater(None).build()

    application.add_handler(_build_conversation_handler())
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    return application