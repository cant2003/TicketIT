import asyncio
from datetime import datetime

from telegram.ext import ConversationHandler

from bot.constants.states import RANGO_FIN
from bot.services import reportes_service as rs
from bot.services import ticket_query as tq
from bot.services.google_sheets_service import export_sheet_as_xlsx
from bot.ui.keyboards import (
    boton_volver,
    boton_volver_menu,
    teclado_periodo,
    teclado_reportes,
)


async def mostrar_menu_reportes(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📊 Selecciona tipo de reporte:",
        reply_markup=teclado_reportes(),
    )


async def mostrar_menu_periodos(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "⏱️ Selecciona el periodo:",
        reply_markup=teclado_periodo(),
    )


async def generar_reportes(origen, context, tickets, nombre_fichero):
    chat_id, responder, editar = _resolver_respuesta(origen)

    if not tickets:
        await _responder_sin_datos(responder, editar)
        return

    msg = await responder(
        "⏳ Generando reporte...",
        reply_markup=boton_volver_menu(),
    )

    archivo = await asyncio.to_thread(export_sheet_as_xlsx)
    archivo.seek(0)

    await msg.edit_text("✅ Reporte generado.")

    await context.bot.send_document(
        chat_id=chat_id,
        document=archivo,
        filename=nombre_fichero,
    )

    await _enviar_copia_correo(archivo, nombre_fichero, responder)


def _resolver_respuesta(origen):
    if hasattr(origen, "message"):
        return (
            origen.message.chat_id,
            origen.message.reply_text,
            origen.edit_message_text,
        )

    return origen.chat_id, origen.reply_text, None


async def _responder_sin_datos(responder, editar):
    if editar:
        await editar("📭 No hay datos para el reporte", reply_markup=boton_volver())
    else:
        await responder("📭 No hay datos para el reporte", reply_markup=boton_volver())


async def _enviar_copia_correo(archivo, nombre_fichero, responder):
    try:
        archivo.seek(0)
        archivo_bytes = archivo.read()

        await asyncio.to_thread(
            rs.enviar_report_correo,
            archivo_bytes,
            nombre_fichero,
        )

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


def nombre_reporte(titulo):
    ahora = datetime.now()
    return f"{titulo} {ahora.strftime('%d-%m-%Y_%H.%M.%S')}.xlsx"


async def reporte_todos(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(tq.tickets_todos)
    await generar_reportes(
        query,
        context,
        tickets,
        nombre_reporte("Reporte Todos Tickets"),
    )


async def reporte_asignado(update, context):
    texto = update.message.text.strip()

    if texto.lower() == "cancelar":
        return ConversationHandler.END

    context.user_data["asignado"] = texto

    tickets = await asyncio.to_thread(tq.tickets_asignado, texto)
    await generar_reportes(
        update.message,
        context,
        tickets,
        nombre_reporte(f"Reporte Tickets Asignados a {texto}"),
    )

    return ConversationHandler.END


async def reporte_usuario(update, context):
    texto = update.message.text.strip()

    if texto.lower() == "cancelar":
        return ConversationHandler.END

    context.user_data["usuario"] = texto

    tickets = await asyncio.to_thread(tq.tickets_usuario, texto)
    await generar_reportes(
        update.message,
        context,
        tickets,
        nombre_reporte(f"Reporte Tickets del Usuario {texto}"),
    )

    return ConversationHandler.END


async def reporte_anyo(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(tq.tickets_ultimo_anyo)
    await generar_reportes(
        query,
        context,
        tickets,
        nombre_reporte("Reporte Ultimos 12 meses"),
    )

    return ConversationHandler.END


async def reporte_mes(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(tq.tickets_ultimo_mes)
    await generar_reportes(
        query,
        context,
        tickets,
        nombre_reporte("Reporte Ultimos 30 Dias"),
    )

    return ConversationHandler.END


async def reporte_hoy(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(tq.tickets_hoy)
    await generar_reportes(
        query,
        context,
        tickets,
        nombre_reporte("Reporte Hoy"),
    )

    return ConversationHandler.END


async def reporte_semana(update, context):
    query = update.callback_query
    await query.answer()

    tickets = await asyncio.to_thread(tq.tickets_semana_actual)
    await generar_reportes(
        query,
        context,
        tickets,
        nombre_reporte("Reporte Ultimos 7 dias"),
    )

    return ConversationHandler.END


async def recibir_inicio(update, context):
    texto = update.message.text.strip()

    if texto.lower() == "cancelar":
        return ConversationHandler.END

    context.user_data["fecha_inicio"] = texto

    await update.message.reply_text("📅 Ingresa fecha fin \nformato 'dd-mm-yyyy':")
    return RANGO_FIN


async def recibir_fin(update, context):
    texto = update.message.text.strip()

    if texto.lower() == "cancelar":
        return ConversationHandler.END

    fecha_inicio = context.user_data.get("fecha_inicio")
    fecha_fin = texto

    try:
        tickets = await asyncio.to_thread(
            tq.tickets_por_rango,
            fecha_inicio,
            fecha_fin,
        )

        nombre_archivo = f"Reporte Periodo {fecha_inicio} Hasta {fecha_fin}.xlsx"
        await generar_reportes(update.message, context, tickets, nombre_archivo)

    except ValueError as e:
        await update.message.reply_text(f"⚠️ {str(e)}")

    return ConversationHandler.END