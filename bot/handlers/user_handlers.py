import threading

from telegram.ext import ConversationHandler

from bot.services import tickets_service
from bot.ui.keyboards import boton_volver, boton_volver_menu


async def recibir_area(update, context):
    if update.message.text.lower() == "cancelar":
        return ConversationHandler.END

    context.user_data["area"] = update.message.text

    await update.message.reply_text(
        "Describe el problema:\n\n(Escribe 'cancelar' para salir)"
    )
    return 1


#!---------------------------------------------------------


async def recibir_descripcion(update, context):
    if update.message.text.lower() == "cancelar":
        return ConversationHandler.END

    data = {
        "usuario": update.message.from_user.first_name,
        "chat_id": update.message.chat_id,
        "area": context.user_data.get("area"),
        "descripcion": update.message.text,
    }

    ticket = tickets_service.crear_ticket(data)

    threading.Thread(target=tickets_service.enviar_correo, args=(ticket.id,)).start()

    await tickets_service.notificar_ti(context, ticket)

    await update.message.reply_text(
        f"✅ Ticket creado ID: {ticket.id}", reply_markup=boton_volver_menu()
    )
    return ConversationHandler.END


#!---------------------------------------------------------


async def ver_estado(update, context):
    try:
        if update.message.text.lower() == "cancelar":
            return ConversationHandler.END

        ticket_id = int(update.message.text)
        ticket = tickets_service.obtener_ticket(ticket_id)

        if not ticket:
            await update.message.reply_text(
                "❌ Ticket no encontrado", reply_markup=boton_volver()
            )
            return ConversationHandler.END

        await update.message.reply_text(f"ID: {ticket.id}\nEstado: {ticket.estado}")

    except Exception:
        await update.message.reply_text("❌ ID inválido", reply_markup=boton_volver())

    return ConversationHandler.END


#!---------------------------------------------------------
