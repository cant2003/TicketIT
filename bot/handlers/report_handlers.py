import asyncio
import threading

from telegram.ext import ConversationHandler

from bot.services import reportes_service as rs
from bot.services import tickets_service as ts
from bot.ui.keyboards import boton_volver, boton_volver_menu

from bot.services.google_sheets_service import export_sheet_as_xlsx

async def mostrar_menu_reportes(update, context):
    query = update.callback_query
    await query.answer()

    from bot.ui.keyboards import teclado_reportes

    await query.edit_message_text(
        "📊 Selecciona tipo de reporte:", reply_markup=teclado_reportes()
    )


async def mostrar_menu_periodos(update, context):
    query = update.callback_query
    await query.answer()

    from bot.ui.keyboards import teclado_periodo

    await query.edit_message_text(
        "⏱️ Selecciona el periodo:", reply_markup=teclado_periodo()
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
            await responder(
                "📭 No hay datos para el reporte", reply_markup=boton_volver()
            )
        return

    msg = await responder("⏳ Generando reporte...", reply_markup=boton_volver_menu())

    archivo = await asyncio.to_thread(export_sheet_as_xlsx)

    if hasattr(archivo, "seek"):
        archivo.seek(0)

    await msg.edit_text("✅ Reporte generado.")

    await context.bot.send_document(
        chat_id=chat_id, document=archivo, filename=nombre_fichero
    )

    try:
        if hasattr(archivo, "seek"):
            archivo.seek(0)
            archivo_bytes = archivo.read()
        else:
            archivo_bytes = archivo

        threading.Thread(
            target=rs.enviar_report_correo,
            args=(archivo_bytes, nombre_fichero),
            daemon=True,
        ).start()

        await responder(
            "📧 Copia de reporte enviada al correo.",
            reply_markup=boton_volver_menu(),
        )

    except Exception as e:
        print(f"Error enviando correo: {e}")
        await responder(
            "⚠️ El reporte falló en el envío por correo.",
            reply_markup=boton_volver_menu(),
        )


#!-----------------------------------------------------------------------
def nombre_reporte(titulo):
    ahora = ts._ahora()
    return f"{titulo} {ahora.strftime('%d-%m-%Y_%H.%M.%S')}.xlsx"


#!---------------------------------------------------------------------
async def reporte_todos(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    tickets = await asyncio.to_thread(rs.tickets_todos)

    titulo = "Reporte Todos Tickets"

    await generar_reportes(query, context, tickets, nombre_reporte(titulo))


#!-------------------------------
async def reporte_asignado(update, context):
    texto = update.message.text.strip()

    if update.message.text.lower() == "cancelar":
        return ConversationHandler.END

    context.user_data["asignado"] = texto

    tickets = await asyncio.to_thread(rs.tickets_asignado, texto)

    titulo = "Reportes Tickest Asignados a {texto}"

    await generar_reportes(update.message, context, tickets, nombre_reporte(titulo))

    return ConversationHandler.END


#!-------------------------------
async def reporte_usuario(update, context):
    texto = update.message.text.strip()

    if update.message.text.lower() == "cancelar":
        return ConversationHandler.END

    context.user_data["usuario"] = texto

    tickets = await asyncio.to_thread(rs.tickets_usuario, texto)

    titulo = f"Reportes Tickest del Usuario {texto}"

    await generar_reportes(update.message, context, tickets, nombre_reporte(titulo))

    return ConversationHandler.END


#!---------------------------------------------------------
async def reporte_anyo(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(rs.tickets_ultimo_anyo)

    titulo = "Reporte Ultimos 12 meses "

    await generar_reportes(query, context, tickets, nombre_reporte(titulo))
    return ConversationHandler.END


#!------------------------------------------------------
async def reporte_mes(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(rs.tickets_ultimo_mes)

    titulo = "Reporte Ultimos 30 Dias"

    await generar_reportes(query, context, tickets, nombre_reporte(titulo))
    return ConversationHandler.END


#!------------------------------------------------------
async def reporte_hoy(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(rs.tickets_hoy)

    titulo = "Reporte Hoy"

    await generar_reportes(query, context, tickets, nombre_reporte(titulo))
    return ConversationHandler.END


#!------------------------------------------------------
async def reporte_semana(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(rs.tickets_semana_actual)

    titulo = "Reporte Ultimos 7 dias"
    await generar_reportes(query, context, tickets, nombre_reporte(titulo))

    return ConversationHandler.END


#!------------------------------------------------------


async def recibir_inicio(update, context):
    if update.message.text.lower() == "cancelar":
        return ConversationHandler.END

    context.user_data["fecha_inicio"] = update.message.text

    await update.message.reply_text("📅 Ingresa fecha fin \nformato 'dd-mm-yyyy':")

    return 7


#!--------------------------------------------------------
async def recibir_fin(update, context):
    if update.message.text.lower() == "cancelar":
        return ConversationHandler.END

    fecha_inicio = context.user_data.get("fecha_inicio")
    fecha_fin = update.message.text

    try:
        tickets = await asyncio.to_thread(rs.tickets_por_rango, fecha_inicio, fecha_fin)

        nombre_archivo = f"Reporte Periodo {fecha_inicio}Hasta{fecha_fin}.xlsx"

        await generar_reportes(update.message, context, tickets, nombre_archivo)

    except ValueError as e:
        await update.message.reply_text(f"⚠️ {str(e)}")

    return ConversationHandler.END
