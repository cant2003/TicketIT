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


def build_application() -> Application:
    application = Application.builder().token(TOKEN).updater(None).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(botones)],
        states={
            AREA: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                    recibir_area,
                )
            ],
            DESCRIPCION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                    recibir_descripcion,
                )
            ],
            ESTADO_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                    ver_estado,
                )
            ],
            OBSERVACION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                    recibir_observacion,
                )
            ],
            ESPERANDO_ASIGNADO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                    reporte_asignado,
                )
            ],
            ESPERANDO_USUARIO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                    reporte_usuario,
                )
            ],
            RANGO_INICIO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                    recibir_inicio,
                )
            ],
            RANGO_FIN: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                    recibir_fin,
                )
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("(?i)^cancelar$"), cancelar_global),
            CommandHandler("cancelar", cancelar_global),
        ],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    return application