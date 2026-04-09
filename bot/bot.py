from bot.config import TOKEN
from bot.ui.keyboards import menu_ti, menu_usuario
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from bot.handlers.common import (
    botones, start, cancelar_global
)
from bot.handlers.user_handlers import (
    recibir_area, recibir_descripcion, ver_estado
)

AREA, DESCRIPCION, ESTADO_ID = range(3)

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