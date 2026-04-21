from telegram.ext import ConversationHandler

from bot.constants.states import (
    AREA,
    ESPERANDO_ASIGNADO,
    ESPERANDO_USUARIO,
    ESTADO_ID,
    RANGO_INICIO,
)
from bot.handlers import report_handlers as rh
from bot.handlers import ti_handlers as th
from bot.ui.keyboards import boton_volver, menu_ti, menu_usuario
from bot.utils import es_ti

TI_ACTIONS = {
    "ver_tickets": th.ver_tickets,
    "en_proceso": th.ver_en_proceso,
    "reporte": rh.mostrar_menu_reportes,
    "rep_todos": rh.reporte_todos,
    "periodo": rh.mostrar_menu_periodos,
    "rep_hoy": rh.reporte_hoy,
    "rep_sem": rh.reporte_semana,
    "rep_mes": rh.reporte_mes,
    "rep_anyo": rh.reporte_anyo,
}


async def start(update, context):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message

    await enviar_menu_inicio(message)


async def enviar_menu_inicio(message):
    chat_id = message.chat_id

    if es_ti(chat_id):
        await message.reply_text("Panel TI 👨‍💻", reply_markup=menu_ti())
    else:
        await message.reply_text(
            "Hola 👋\nEn que puedo ayudarte",
            reply_markup=menu_usuario(),
        )


async def editar_menu_inicio(query):
    chat_id = query.message.chat_id

    if es_ti(chat_id):
        await query.edit_message_text("Panel TI 👨‍💻", reply_markup=menu_ti())
    else:
        await query.edit_message_text(
            "Hola 👋\nEn que puedo ayudarte",
            reply_markup=menu_usuario(),
        )


async def botones(update, context):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    if data == "menu":
        await editar_menu_inicio(query)
        return

    if data == "menu_message":
        await enviar_menu_inicio(query.message)
        return

    if es_ti(chat_id):
        return await manejar_accion_ti(update, context, data)

    return await manejar_accion_usuario(query, data)


async def manejar_accion_ti(update, context, data):
    query = update.callback_query

    if data in TI_ACTIONS:
        return await TI_ACTIONS[data](update, context)

    if data.startswith("ticket_"):
        return await th.ver_ticket_detalle(update, context)

    if data.startswith("tomar_"):
        return await th.tomar_ticket_handler(update, context)

    if data.startswith("cerrar_"):
        return await th.cerrar_ticket_handler(update, context)

    if data == "rep_asig":
        await query.message.reply_text("👤 Ingresa el nombre del Asignado TI:")
        return ESPERANDO_ASIGNADO

    if data == "rep_user":
        await query.message.reply_text("👤 Ingresa el nombre del Usuario")
        return ESPERANDO_USUARIO

    if data == "rep_per":
        await query.edit_message_text(
            "📅 Ingresa fecha inicio\n formato (dd-mm-yyyy):\n\n"
            "(Escribe 'cancelar' para salir)"
        )
        return RANGO_INICIO

    return ConversationHandler.END


async def manejar_accion_usuario(query, data):
    if data == "crear":
        await query.edit_message_text("Escribe el AREA:")
        return AREA

    if data == "estado":
        await query.edit_message_text("Escribe ID:")
        return ESTADO_ID

    return ConversationHandler.END


async def cancelar_global(update, context):
    if update.message:
        await update.message.reply_text(
            "❌ Operación cancelada",
            reply_markup=boton_volver(),
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "❌ Operación cancelada",
            reply_markup=boton_volver(),
        )

    context.user_data.clear()
    return ConversationHandler.END