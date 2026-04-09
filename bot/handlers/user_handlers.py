from bot.services import tickets_service
from telegram.ext import ConversationHandler



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
    area = context.user_data.get("area")

    if update.message.text.lower() == "cancelar":
        return ConversationHandler.END
    
    data = {
        "usuario": update.message.from_user.first_name,
        "chat_id": update.message.chat_id,
        "area": context.user_data["area"],
        "descripcion": update.message.text
    }

    ticket = tickets_service.crear_ticket(data)

    await update.message.reply_text(f"✅ Ticket creado ID: {ticket.id}")
    return ConversationHandler.END
#!---------------------------------------------------------

async def ver_estado(update, context):
    try:
        ticket_id = int(update.message.text)
        ticket = tickets_service.obtener_ticket(ticket_id)

        if update.message.text.lower() == "cancelar":
            return ConversationHandler.END

        if not ticket:
            await update.message.reply_text("❌ Ticket no encontrado")
            return ConversationHandler.END

        await update.message.reply_text(
            f"ID: {ticket.id}\nEstado: {ticket.estado}"
        )

    except:
        await update.message.reply_text("❌ ID inválido")
        return ConversationHandler.END
#!---------------------------------------------------------
