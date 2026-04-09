from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from bot.config import TOKEN
from bot.handlers.common import botones,start
from bot.handlers.user_handlers import (
    recibir_area, recibir_descripcion, ver_estado
)
from bot.ui.keyboards import menu_ti, menu_usuario

AREA, DESCRIPCION, ESTADO_ID = range(3)

app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(botones)],
    states={
        AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_area)],
        DESCRIPCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_descripcion)],
        ESTADO_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ver_estado)],
    },
    fallbacks=[],
)

app.add_handler(conv_handler)
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
app.run_polling()