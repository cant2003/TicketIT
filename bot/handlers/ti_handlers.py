from bot.services import tickets_service
from bot.ui.keyboards import teclado_tickets, teclado_ticket_detalle, boton_volver, boton_volver_menu,teclado_detalle_proceso
from telegram.ext import ConversationHandler
from bot.constants.states import OBSERVACION
from bot.services import reportes_service
import threading

# ! ver tickets 
async def ver_tickets(update, context):
    query = update.callback_query
    await query.answer()

    tickets = tickets_service.obtener_tickets_abiertos()

    if not tickets:
        await query.edit_message_text("📭 No hay tickets", reply_markup=boton_volver() )
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
        await query.edit_message_text("📭 No tienes tickets en proceso", reply_markup=boton_volver() )
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

    try:
        ticket_id = int(query.data.split("_")[1])
    except:
        await query.edit_message_text("❌ Error en el ID", reply_markup=boton_volver())
        return
    
    ticket = tickets_service.obtener_ticket(ticket_id)

    if not ticket:
        await query.edit_message_text("❌ Ticket no encontrado", reply_markup=boton_volver() )
        return

    texto = (
        f"🎫 Ticket #{ticket.id}\n"
        f"Usuario: {ticket.usuario}\n"
        f"Área: {ticket.area}\n"
        f"Descripción: {ticket.descripcion}\n"
        f"Estado: {ticket.estado}\n"
        f"Asignado: {ticket.asignado_a or 'Nadie'}"
    )
    if ticket.estado == 'En Proceso':
        await query.edit_message_text(
            texto, reply_markup=teclado_detalle_proceso(ticket.id)
        )
    else:
        await query.edit_message_text(
            texto,
            reply_markup=teclado_ticket_detalle(ticket.id)
        )
#!---------------------------------------------------------

#! tomar tickets
async def tomar_ticket_handler(update, context):
    query = update.callback_query
    await query.answer()

    try:
        ticket_id = int(query.data.split("_")[1])
    except:
        await query.edit_message_text("❌ Error en el ID", reply_markup=boton_volver())
        return
    
    usuario = query.from_user.first_name

    try:
        ticket = tickets_service.tomar_ticket(ticket_id, usuario)

        await query.edit_message_text(
            f"🔧 Ticket #{ticket.id} tomado", reply_markup=boton_volver_menu()
        )
        chat_id = int(ticket.chat_id) if ticket.chat_id else None
        await context.bot.send_message(
            chat_id,
            f"👨‍💻 Tu ticket está en proceso", reply_markup=boton_volver()
        )
    
    except ValueError as e:
        await query.edit_message_text(f"⚠️ {str(e)}", reply_markup=boton_volver())
    
    except Exception:
        await query.edit_message_text("❌ Error inesperado", reply_markup=boton_volver())
#!---------------------------------------------------------

# !  Cerrar ticket
async def cerrar_ticket_handler(update, context):
    query = update.callback_query
    await query.answer()

    try:
        ticket_id = int(query.data.split("_")[1])
    except:
        await query.edit_message_text("❌ Error en el ID", reply_markup=boton_volver())
        return
    
    context.user_data["cerrar_ticket_id"] = ticket_id

    await query.edit_message_text(
        "✍️ Escribe una observación para cerrar el ticket:\n\n(Escribe 'cancelar' para salir)"
    )
    
    return OBSERVACION
#! -----------------------------------------------
async def recibir_observacion(update, context):
    observacion = update.message.text
    ticket_id = context.user_data.get("cerrar_ticket_id")

    if observacion.lower() == "cancelar":
        return ConversationHandler.END

    if not ticket_id:
        await update.message.reply_text("❌ Error, vuelve a empezar", reply_markup=boton_volver())
        return ConversationHandler.END

    usuario = update.message.from_user.first_name

    try:
        ticket = tickets_service.cerrar_ticket_con_observacion(
            ticket_id, observacion, usuario
        )

        await update.message.reply_text(
            f"✅ Ticket #{ticket.id} cerrado\n📝 Observación guardada", reply_markup=boton_volver_menu()
        )
        chat_id = int(ticket.chat_id) if ticket.chat_id else None
        await context.bot.send_message(
            chat_id,
            f"✅ Tu ticket fue Atendido\n📝 Observación: {observacion}",reply_markup=boton_volver_menu()
        )

    except ValueError as e:
        await update.message.reply_text(f"⚠️ {str(e)}")

    return ConversationHandler.END
#! -----------------------------------------------

async def mostrar_menu_reportes(update, context):
    query = update.callback_query
    await query.answer()

    from bot.ui.keyboards import teclado_reportes

    await query.edit_message_text(
        "📊 Selecciona tipo de reporte:",
        reply_markup=teclado_reportes()
    )

async def mostrar_menu_periodos(update, context):
    query = update.callback_query
    await query.answer()

    from bot.ui.keyboards import teclado_periodo

    await query.edit_message_text(
        "⏱️ Selecciona el periodo:",
        reply_markup=teclado_periodo()
    )

#!---------------------------------------------------------
async def generar_reportes(origen, context, tickets, nombre_fichero):

    if hasattr(origen, "message"): 
        chat_id = origen.message.chat_id
        responder = origen.message.reply_text
        editar = origen.edit_message_text
    else: 
        chat_id = origen.chat_id
        responder = origen.reply_text
        editar = None

    if not tickets:
        if editar:
            await editar("📭 No hay datos para el reporte", reply_markup=boton_volver())
        else:
            await responder("📭 No hay datos para el reporte", reply_markup=boton_volver())
        return

    archivo = reportes_service.generar_excel(tickets)

    if hasattr(archivo, 'seek'):
        archivo.seek(0)

    await context.bot.send_document(
        chat_id=chat_id,
        document=archivo,
        filename=nombre_fichero
    )

    try:
        if hasattr(archivo, 'seek'):
            archivo.seek(0)
            archivo_bytes = archivo.read()
        else:
            archivo_bytes = archivo

        threading.Thread(
            target=reportes_service.enviar_report_correo,
            args=(archivo_bytes, nombre_fichero),
            daemon=True
        ).start()

        await responder(
            "📧 Copia de reporte se está enviando al correo...",
            reply_markup=boton_volver_menu()
        )

    except Exception as e:
        print(f"Error enviando correo: {e}")
        await responder(
            "⚠️ El reporte falló en el envío por correo.",
            reply_markup=boton_volver_menu()
        )

#!-----------------------------------------------------------------------
async def reporte_todos(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    tickets = reportes_service.tickets_todos()
    fecha, hora = tickets_service._ahora()

    nombre_archivo = f"Reporte Todos Tickets {fecha}_{hora}.xlsx"

    await generar_reportes(
        query,
        context,
        tickets,
        nombre_archivo
    )

#!-------------------------------
async def reporte_asignado(update,context):
    texto = update.message.text.strip()

    if update.message.text.lower() == "cancelar":
        return ConversationHandler.END
    
    context.user_data["asignado"] = texto

    tickets = reportes_service.tickets_asignado(texto)

    fecha,hora = tickets_service._ahora()

    nombre_archivo = f"Reportes Tickest Asignados a {texto} {fecha}_{hora}.xlsx"

    await generar_reportes(update.message, context, tickets, nombre_archivo)

    return ConversationHandler.END

#!-------------------------------
async def reporte_usuario(update,context):
    texto = update.message.text.strip()

    if update.message.text.lower() == "cancelar":
        return ConversationHandler.END
    
    context.user_data["usuario"] = texto

    tickets = reportes_service.tickets_usuario(texto)

    fecha,hora = tickets_service._ahora()

    nombre_archivo = f"Reportes Tickest del Usuario {texto} {fecha}_{hora}.xlsx"

    await generar_reportes(update.message, context, tickets, nombre_archivo)

    return ConversationHandler.END
    