from bot.config import TOKEN
from bot.constants.states import (AREA, DESCRIPCION, ESTADO_ID, OBSERVACION, ESPERANDO_ASIGNADO,ESPERANDO_USUARIO)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from bot.handlers.common import (
    botones, start, cancelar_global
)
from bot.handlers.user_handlers import (
    recibir_area, recibir_descripcion, ver_estado, 
)
from bot.handlers.ti_handlers import (
    recibir_observacion,reporte_asignado, reporte_usuario
)

app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(botones)],
    states={
        AREA: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                recibir_area
            )
        ],
        DESCRIPCION: [
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
            recibir_descripcion
            )
        ],
        ESTADO_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                ver_estado
            )
        ],
        OBSERVACION: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"),
                recibir_observacion
            )
        ],
        ESPERANDO_ASIGNADO:[
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"), reporte_asignado
            )
        ],
        ESPERANDO_USUARIO: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.Regex("(?i)^cancelar$"), reporte_usuario
            )
        ],

    },
    fallbacks=[
        MessageHandler(filters.Regex("(?i)^cancelar$"), cancelar_global),
        CommandHandler("cancelar", cancelar_global),
    ]
)

app.add_handler(conv_handler)
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
app.run_polling()