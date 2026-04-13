from bot.handlers import (ti_handlers)
from bot.utils import es_ti
from bot.ui.keyboards import (menu_ti, menu_usuario)
from telegram.ext import ConversationHandler


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def start(update, context):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message

    chat_id = message.chat_id

    if es_ti(chat_id):
        await message.reply_text(
            "Panel TI 👨‍💻",
            reply_markup=menu_ti()
        )
    else:
        await message.reply_text(
            "Hola 👋",
            reply_markup=menu_usuario()
        )
#!---------------------------------------------------------

async def botones(update, context):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    
    if data == "menu":
        if es_ti(chat_id):
            await query.edit_message_text(
                "Panel TI 👨‍💻",
                reply_markup=menu_ti()
            )
        else:
            await query.edit_message_text(
                "Hola 👋",
                reply_markup=menu_usuario()
            )
        return

    if es_ti(chat_id):
        if data == "ver_tickets":
            return await ti_handlers.ver_tickets(update, context)

        elif data == "en_proceso":
            return await ti_handlers.ver_en_proceso(update, context)

        elif data.startswith("ticket_"):
            return await ti_handlers.ver_ticket_detalle(update, context)

        elif data.startswith("tomar_"):
            return await ti_handlers.tomar_ticket_handler(update, context)

        elif data.startswith("cerrar_"):
            return await ti_handlers.cerrar_ticket_handler(update, context)
        
        elif data == "reporte":
            return await ti_handlers.mostrar_menu_reportes(update, context)

        elif data == "rep_todos":
            return await ti_handlers.reporte_todos(update, context)

    else:
        if data == "crear":
            await query.edit_message_text("Escribe el AREA:")
            return 0

        elif data == "estado":
            await query.edit_message_text("Escribe ID:")
            return 2
# !---------------------------------------------------------

async def cancelar_global(update, context):
    if update.message:
        await update.message.reply_text(
            "❌ Operación cancelada",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙Volver al inicio", callback_data="menu")]
            ])
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "❌ Operación cancelada",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Volver al inicio", callback_data="menu")]
            ])
        )
    context.user_data.clear()

    return ConversationHandler.END