from telegram.ext import ConversationHandler

from bot.handlers import report_handlers as rh
from bot.handlers import ti_handlers as th
from bot.ui.keyboards import boton_volver, menu_ti, menu_usuario
from bot.utils import es_ti


async def start(update, context):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message

    chat_id = message.chat_id

    if es_ti(chat_id):
        await message.reply_text("Panel TI 👨‍💻", reply_markup=menu_ti())
    else:
        await message.reply_text(
            "Hola 👋\nEn que puedo ayudarte", reply_markup=menu_usuario()
        )


#!---------------------------------------------------------

MAPA_TI = {
    "ver_tickets": th.ver_tickets,
    "en_proceso": th.ver_en_proceso,
}


async def botones(update, context):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    # !MENUS -----------------------------
    if data == "menu":
        if es_ti(chat_id):
            await query.edit_message_text("Panel TI 👨‍💻", reply_markup=menu_ti())
        else:
            await query.edit_message_text(
                "Hola 👋\nEn que puedo ayudarte", reply_markup=menu_usuario()
            )
        return

    if data == "menu_message":
        if es_ti(chat_id):
            await query.message.reply_text("Panel TI 👨‍💻", reply_markup=menu_ti())
        else:
            await query.message.reply_text(
                "Hola 👋\nEn que puedo ayudarte", reply_markup=menu_usuario()
            )
        return

    # ! TI------------------------------------------------

    if es_ti(chat_id):
        if data in MAPA_TI:
            return await MAPA_TI[data](update, context)

        elif data.startswith("ticket_"):
            return await th.ver_ticket_detalle(update, context)

        elif data.startswith("tomar_"):
            return await th.tomar_ticket_handler(update, context)

        elif data.startswith("cerrar_"):
            return await th.cerrar_ticket_handler(update, context)

        elif data == "reporte":
            return await rh.mostrar_menu_reportes(update, context)

        elif data == "rep_todos":
            return await rh.reporte_todos(update, context)

        elif data == "rep_asig":
            await query.message.reply_text("👤 Ingresa el nombre del Asignado TI:")
            return 4

        elif data == "rep_user":
            await query.message.reply_text("👤 Ingresa el nombre del Usuario")
            return 5

        elif data == "periodo":
            return await rh.mostrar_menu_periodos(update, context)

        elif data == "rep_hoy":
            return await rh.reporte_hoy(update, context)

        elif data == "rep_sem":
            return await rh.reporte_semana(update, context)

        elif data == "rep_mes":
            return await rh.reporte_mes(update, context)

        elif data == "rep_anyo":
            return await rh.reporte_anyo(update, context)

        elif data == "rep_per":
            await query.edit_message_text(
                "📅 Ingresa fecha inicio\n formato (dd-mm-yyyy):\n\n(Escribe 'cancelar' para salir)"
            )
            return 6

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
            "❌ Operación cancelada", reply_markup=boton_volver()
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "❌ Operación cancelada", reply_markup=boton_volver()
        )
    context.user_data.clear()

    return ConversationHandler.END
