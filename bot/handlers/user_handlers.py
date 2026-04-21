import asyncio

from telegram.ext import ConversationHandler

from bot.constants.states import DESCRIPCION
from bot.services import tickets_service
from bot.ui.keyboards import boton_volver, boton_volver_menu


async def recibir_area(update, context):
    texto = update.message.text.strip()

    if texto.lower() == "cancelar":
        return ConversationHandler.END

    context.user_data["area"] = texto

    await update.message.reply_text(
        "Describe el problema:\n\n(Escribe 'cancelar' para salir)"
    )

    return DESCRIPCION


async def recibir_descripcion(update, context):
    texto = update.message.text.strip()

    if texto.lower() == "cancelar":
        return ConversationHandler.END

    data = {
        "usuario": update.message.from_user.first_name,
        "chat_id": update.message.chat_id,
        "area": context.user_data.get("area"),
        "descripcion": texto,
    }

    ticket = await asyncio.to_thread(tickets_service.crear_ticket, data)

    asyncio.create_task(
        asyncio.to_thread(tickets_service.enviar_correo, ticket.id)
    )

    await tickets_service.notificar_ti(context, ticket)

    await update.message.reply_text(
        f"✅ Ticket creado ID: {ticket.id}",
        reply_markup=boton_volver_menu(),
    )

    return ConversationHandler.END


async def ver_estado(update, context):
    texto = update.message.text.strip()

    if texto.lower() == "cancelar":
        return ConversationHandler.END

    try:
        ticket_id = int(texto)
    except ValueError:
        await update.message.reply_text("❌ ID inválido", reply_markup=boton_volver())
        return ConversationHandler.END

    ticket = await asyncio.to_thread(tickets_service.obtener_ticket, ticket_id)

    if not ticket:
        await update.message.reply_text(
            "❌ Ticket no encontrado",
            reply_markup=boton_volver(),
        )
        return ConversationHandler.END

    await update.message.reply_text(f"ID: {ticket.id}\nEstado: {ticket.estado}")

    return ConversationHandler.END