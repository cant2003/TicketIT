import asyncio

from telegram.ext import ConversationHandler

from bot.constants.states import OBSERVACION
from bot.services.tickets_service import (
    cerrar_ticket_con_observacion,
    obtener_ticket,
    obtener_tickets_abiertos,
    obtener_tickets_en_proceso,
    tomar_ticket,
)
from bot.ui.keyboards import (
    boton_volver,
    boton_volver_menu,
    teclado_detalle_proceso,
    teclado_ticket_detalle,
    teclado_tickets,
)


def _extraer_ticket_id(callback_data: str):
    try:
        return int(callback_data.split("_")[1])
    except (IndexError, ValueError):
        return None


def _formatear_detalle_ticket(ticket):
    return (
        f"🎫 Ticket #{ticket.id}\n"
        f"Usuario: {ticket.usuario}\n"
        f"Área: {ticket.area}\n"
        f"Descripción: {ticket.descripcion}\n"
        f"Estado: {ticket.estado}\n"
        f"Asignado: {ticket.asignado_a or 'Nadie'}"
    )


async def ver_tickets(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(obtener_tickets_abiertos)

    if not tickets:
        await query.edit_message_text("📭 No hay tickets", reply_markup=boton_volver())
        return

    await query.edit_message_text(
        "📋 Tickets disponibles:",
        reply_markup=teclado_tickets(tickets),
    )


async def ver_en_proceso(update, context):
    query = update.callback_query
    await query.answer()

    usuario = query.from_user.first_name
    tickets = await asyncio.to_thread(
        obtener_tickets_en_proceso,
        usuario,
    )

    if not tickets:
        await query.edit_message_text(
            "📭 No tienes tickets en proceso",
            reply_markup=boton_volver(),
        )
        return

    await query.edit_message_text(
        "🔧 Tus tickets:",
        reply_markup=teclado_tickets(tickets),
    )


async def ver_ticket_detalle(update, context):
    query = update.callback_query
    await query.answer()

    ticket_id = _extraer_ticket_id(query.data)

    if ticket_id is None:
        await query.edit_message_text("❌ Error en el ID", reply_markup=boton_volver())
        return

    ticket = await asyncio.to_thread(obtener_ticket, ticket_id)

    if not ticket:
        await query.edit_message_text(
            "❌ Ticket no encontrado",
            reply_markup=boton_volver(),
        )
        return

    texto = _formatear_detalle_ticket(ticket)

    if ticket.estado == "En Proceso":
        reply_markup = teclado_detalle_proceso(ticket.id)
    else:
        reply_markup = teclado_ticket_detalle(ticket.id)

    await query.edit_message_text(texto, reply_markup=reply_markup)


async def tomar_ticket_handler(update, context):
    query = update.callback_query
    await query.answer()

    ticket_id = _extraer_ticket_id(query.data)

    if ticket_id is None:
        await query.edit_message_text("❌ Error en el ID", reply_markup=boton_volver())
        return

    usuario = query.from_user.first_name
    telegram_id = query.from_user.id

    try:
        ticket = await asyncio.to_thread(
            tomar_ticket,
            ticket_id,
            usuario,
            telegram_id,
        )

        await query.edit_message_text(
            f"🔧 Ticket #{ticket.id} tomado",
            reply_markup=boton_volver_menu(),
        )

        chat_id = int(ticket.chat_id) if ticket.chat_id else None
        if chat_id:
            await context.bot.send_message(
                chat_id,
                "👨‍💻 Tu ticket está en proceso",
                reply_markup=boton_volver(),
            )

    except ValueError as e:
        await query.edit_message_text(f"⚠️ {str(e)}", reply_markup=boton_volver())

    except Exception as e:
        print(f"Error inesperado al tomar ticket: {e}")
        await query.edit_message_text(
            "❌ Error inesperado",
            reply_markup=boton_volver(),
        )


async def cerrar_ticket_handler(update, context):
    query = update.callback_query
    await query.answer()

    ticket_id = _extraer_ticket_id(query.data)

    if ticket_id is None:
        await query.edit_message_text("❌ Error en el ID", reply_markup=boton_volver())
        return

    context.user_data["cerrar_ticket_id"] = ticket_id

    await query.edit_message_text(
        "✍️ Escribe una observación para cerrar el ticket:\n\n"
        "(Escribe 'cancelar' para salir)"
    )

    return OBSERVACION


async def recibir_observacion(update, context):
    observacion = update.message.text.strip()
    ticket_id = context.user_data.get("cerrar_ticket_id")

    if observacion.lower() == "cancelar":
        return ConversationHandler.END

    if not ticket_id:
        await update.message.reply_text(
            "❌ Error, vuelve a empezar",
            reply_markup=boton_volver(),
        )
        return ConversationHandler.END

    usuario = update.message.from_user.first_name
    telegram_id = update.message.from_user.id

    try:
        ticket = await asyncio.to_thread(
            cerrar_ticket_con_observacion,
            ticket_id,
            observacion,
            usuario,
            telegram_id,
        )

        await update.message.reply_text(
            f"✅ Ticket #{ticket.id} cerrado\n📝 Observación guardada",
            reply_markup=boton_volver_menu(),
        )

        chat_id = int(ticket.chat_id) if ticket.chat_id else None
        if chat_id:
            await context.bot.send_message(
                chat_id,
                f"✅ Tu ticket fue Atendido\n📝 Observación: {observacion}",
                reply_markup=boton_volver_menu(),
            )

    except ValueError as e:
        await update.message.reply_text(f"⚠️ {str(e)}")

    except Exception as e:
        print(f"Error inesperado al cerrar ticket: {e}")
        await update.message.reply_text(
            "❌ Error inesperado al cerrar el ticket",
            reply_markup=boton_volver(),
        )

    return ConversationHandler.END