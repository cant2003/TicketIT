from bot.services import tickets_service

async def recibir_area(update, context):
    context.user_data["area"] = update.message.text
    await update.message.reply_text("Describe el problema:")
    return 1
#!---------------------------------------------------------

async def recibir_descripcion(update, context):
    data = {
        "usuario": update.message.from_user.first_name,
        "chat_id": update.message.chat_id,
        "area": context.user_data["area"],
        "descripcion": update.message.text
    }

    ticket = tickets_service.crear_ticket(data)

    await update.message.reply_text(f"✅ Ticket creado ID: {ticket.id}")
    return -1
#!---------------------------------------------------------

async def ver_estado(update, context):
    try:
        ticket_id = int(update.message.text)
        ticket = tickets_service.obtener_ticket(ticket_id)

        if not ticket:
            await update.message.reply_text("❌ Ticket no encontrado")
            return -1

        await update.message.reply_text(
            f"ID: {ticket.id}\nEstado: {ticket.estado}"
        )

    except:
        await update.message.reply_text("❌ ID inválido")