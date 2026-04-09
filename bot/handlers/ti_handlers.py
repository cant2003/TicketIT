from bot.services import tickets_service
from bot.ui.keyboards import teclado_tickets, teclado_ticket_detalle

# ! ver tickets 
async def ver_tickets(update, context):
    query = update.callback_query
    await query.answer()

    tickets = tickets_service.obtener_tickets_abiertos()

    if not tickets:
        await query.edit_message_text("📭 No hay tickets")
        return

    await query.edit_message_text(
        "📋 Tickets disponibles:",
        reply_markup=teclado_tickets(tickets)
    )
#!---------------------------------------------------------

#! Listar en proceso
async def ver_en_proceso(update, context):
    query = update.callback_query
    await query.answer()

    usuario = query.from_user.first_name
    tickets = tickets_service.obtener_tickets_en_proceso(usuario)

    if not tickets:
        await query.edit_message_text("📭 No tienes tickets en proceso")
        return

    await query.edit_message_text(
        "🔧 Tus tickets:",
        reply_markup=teclado_tickets(tickets)
    )
#!---------------------------------------------------------

# ! Ver detalle ticket 
async def ver_ticket_detalle(update, context):
    query = update.callback_query
    await query.answer()

    ticket_id = int(query.data.split("_")[1])
    ticket = tickets_service.obtener_ticket(ticket_id)

    if not ticket:
        await query.edit_message_text("❌ Ticket no encontrado")
        return

    texto = (
        f"🎫 Ticket #{ticket.id}\n"
        f"Usuario: {ticket.usuario}\n"
        f"Área: {ticket.area}\n"
        f"Descripción: {ticket.descripcion}\n"
        f"Estado: {ticket.estado}\n"
        f"Asignado: {ticket.asignado_a or 'Nadie'}"
    )

    await query.edit_message_text(
        texto,
        reply_markup=teclado_ticket_detalle(ticket.id)
    )
#!---------------------------------------------------------

#! tomar tickets
async def tomar_ticket_handler(update, context):
    query = update.callback_query
    await query.answer()

    ticket_id = int(query.data.split("_")[1])
    usuario = query.from_user.first_name

    try:
        ticket = tickets_service.tomar_ticket(ticket_id, usuario)

        await query.edit_message_text(
            f"🔧 Ticket #{ticket.id} tomado"
        )
        await context.bot.send_message(
            int(ticket.chat_id),
            f"👨‍💻 Tu ticket está en proceso"
        )
    
    except ValueError as e:
        await query.edit_message_text(f"⚠️ {str(e)}")
    
    except Exception:
        await query.edit_message_text("❌ Error inesperado")
#!---------------------------------------------------------

# !  Cerrar ticket
async def cerrar_ticket_handler(update, context):
    query = update.callback_query
    await query.answer()

    ticket_id = int(query.data.split("_")[1])

    try:
        ticket = tickets_service.cerrar_ticket(ticket_id)

        await query.edit_message_text(f"✅ Ticket #{ticket.id} cerrado")

        await context.bot.send_message(
            int(ticket.chat_id),
            "🎉 Tu ticket fue resuelto"
        )

    except ValueError as e:
        await query.edit_message_text(f"⚠️ {str(e)}")

    except Exception:
        await query.edit_message_text("❌ Error inesperado")
#!---------------------------------------------------------

