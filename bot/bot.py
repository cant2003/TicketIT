from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters, ConversationHandler
)
from backend.db import SessionLocal, Ticket
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

directorio_actual = Path(__file__).resolve().parent
ruta_env = directorio_actual.parent / '.env'

load_dotenv(dotenv_path=ruta_env)


TOKEN = os.getenv("TELEGRAM_TOKEN")

USUARIOS_TI = [
    os.getenv("CRISTIAN_ID"), # !Cristian
    ]

AREA, DESCRIPCION, ESTADO_ID = range(3)

#! __________________Verificacion TI__________________ 
def es_ti(chat_id):
    return chat_id in USUARIOS_TI

#! __________________Menu inicio____________________
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message

    chat_id = message.chat_id

    if es_ti(chat_id):
        keyboard = [
            [InlineKeyboardButton("📋 Ver Tickets", callback_data="ver_tickets")],
            [InlineKeyboardButton("🔧 En Proceso", callback_data="en_proceso")],
        ]
        mensaje = "<b>Panel TI 👨‍💻</b>\nSelecciona una opción:" #!MENSAJE
    else:
        keyboard = [
            [InlineKeyboardButton("🎫 Crear Ticket", callback_data="crear")],
            [InlineKeyboardButton("📄 Ver Estado", callback_data="estado")]
        ]
        mensaje = "<b>¡Hola! 👋</b>\n¿En qué puedo ayudarte?" #!MENSAJE

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(mensaje, parse_mode='HTML', reply_markup=reply_markup)

#! __________________BOTONES__________________

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id

    if es_ti(chat_id):
        return await botones_ti(update, context)
    else:
        return await botones_usuario(update, context)
#! -----------------------------    
async def botones_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "crear":
        await query.edit_message_text("Escribe el AREA del problema:")
        return AREA

    elif query.data == "estado":
        await query.edit_message_text("Escribe el ID del ticket:")
        return ESTADO_ID
    return 
#! ---------------------------  
async def botones_ti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "ver_tickets":
        db = SessionLocal()
        tickets = db.query(Ticket).filter(Ticket.estado == "Abierto").all()
        db.close()

        if not tickets:
            await query.edit_message_text("📭 No hay tickets disponibles")
            return ConversationHandler.END

        keyboard = []

        for t in tickets:
            keyboard.append([
                InlineKeyboardButton(f"#{t.id} | {t.area} | {t.descripcion[:20]}...", callback_data=f"ticket_{t.id}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="menu_ti")])

        await query.edit_message_text(
            "📋 Tickets disponibles:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    elif query.data == "en_proceso":
        usuario_ti = query.from_user.first_name

        db = SessionLocal()
        tickets = db.query(Ticket).filter(
            Ticket.estado == "En Proceso",
            Ticket.asignado_a == usuario_ti
        ).all()
        db.close()

        if not tickets:
            await query.edit_message_text("📭 No tienes tickets en proceso")
            return ConversationHandler.END
        keyboard = []
        
        for t in tickets:
            texto = f"#{t.id} | {t.area} | {t.estado}"
            keyboard.append([
            InlineKeyboardButton(texto, callback_data=f"ticket_{t.id}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="menu_ti")])

        await query.edit_message_text(
            "🔧 Tus tickets en proceso:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    elif query.data.startswith("ticket_"):
        ticket_id = int(query.data.split("_")[1])

        db = SessionLocal()
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        db.close()

        if not ticket:
            await query.edit_message_text("❌ Ticket no encontrado")
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton("🔧 Tomar", callback_data=f"tomar_{ticket_id}")],
            [InlineKeyboardButton("✅ Cerrar", callback_data=f"cerrar_{ticket_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data="ver_tickets")]
        ]
        texto = (
            f"🎫 Ticket #{ticket.id}\n"
            f"Usuario: {ticket.usuario}\n"
            f"Área: {ticket.area}\n"
            f"Descripción: {ticket.descripcion}\n"
            f"Estado: {ticket.estado}\n"
            f"Asignado: {ticket.asignado_a or 'Nadie'}\n"
            f"Creado: {ticket.fecha_creacion} {ticket.hora_creacion}"
        )

        await query.edit_message_text(texto, reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    elif query.data.startswith("tomar_"):
        ticket_id = int(query.data.split("_")[1])
        usuario_ti = query.from_user.first_name

        db = SessionLocal()
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if ticket.estado == "En Proceso":
            db.close()
            await query.edit_message_text("⚠️ Este ticket ya está en proceso")
            return ConversationHandler.END
        
        ticket.estado = "En Proceso"
        ticket.asignado_a = usuario_ti

        ahora = datetime.now()
        ticket.fecha_actualizacion = ahora.strftime("%d-%m-%Y")
        ticket.hora_actualizacion = ahora.strftime("%H:%M:%S")

        db.commit()
        chat_usuario = int(ticket.chat_id)
        db.close()

        await query.edit_message_text(f"🔧 Ticket #{ticket_id} tomado por {usuario_ti}")

        await context.bot.send_message(
            chat_usuario,
            f"👨‍💻 Tu ticket #{ticket_id} está siendo atendido por {usuario_ti}"
        )
        return ConversationHandler.END
    
    elif query.data.startswith("cerrar_"):
        ticket_id = int(query.data.split("_")[1])

        db = SessionLocal()
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            db.close()
            await query.edit_message_text("❌ Ticket no encontrado")
            return ConversationHandler.END

        ticket.estado = "Cerrado"

        ahora = datetime.now()
        ticket.fecha_actualizacion = ahora.strftime("%d-%m-%Y")
        ticket.hora_actualizacion = ahora.strftime("%H:%M:%S")

        db.commit()
        chat_usuario = int(ticket.chat_id)
        db.close()

        await query.edit_message_text(f"✅ Ticket #{ticket_id} cerrado")

        await context.bot.send_message(
            chat_usuario,
            f"🎉 Tu ticket #{ticket_id} ha sido resuelto"
        )

        return ConversationHandler.END
    
    elif query.data == "menu_ti":
        return await start(update, context)

    return ConversationHandler.END

#! __________________Crear ticket__________________
async def recibir_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["area"] = update.message.text
    await update.message.reply_text("Describe el problema:")                        #! Mensaje
    return DESCRIPCION

async def recibir_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.message.from_user.first_name
    chat_id = update.message.chat_id
    area = context.user_data["area"]
    descripcion = update.message.text

    #! Crear ticket en SQLite
    db = SessionLocal()
    ahora = datetime.now()
    ticket = Ticket(
        usuario=usuario,
        area=area,
        descripcion=descripcion,
        estado="Abierto",
        fecha_creacion=ahora.strftime("%d-%m-%Y"),
        hora_creacion=ahora.strftime("%H:%M:%S"),
        fecha_actualizacion=ahora.strftime("%d-%m-%Y"),
        hora_actualizacion=ahora.strftime("%H:%M:%S"),
        chat_id=str(chat_id)
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    db.close()

    #! Notificar al usuario
    await update.message.reply_text(f"✅ Ticket creado ID: {ticket.id}") #! Mensaje

    #! Notificar al equipo TI
    for ti_id in USUARIOS_TI:
        await context.bot.send_message(
            chat_id=ti_id,
            text=f"🛠 Nuevo ticket #{ticket.id}\nUsuario: {usuario}\nÁrea: {area}\nDescripción: {descripcion}\nEstado: Abierto" #! Mensaje
        )

    return ConversationHandler.END

#! __________________VER ESTADO__________________
async def ver_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticket_id = int(update.message.text)
        db = SessionLocal()
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        db.close()

        if ticket:
            await update.message.reply_text(
                f"ID: {ticket.id}\nUsuario: {ticket.usuario}\nÁrea: {ticket.area}\nDescripción: {ticket.descripcion}\nEstado: {ticket.estado}\nCreado: {ticket.fecha_creacion} {ticket.hora_creacion}\nActualizado: {ticket.fecha_actualizacion} {ticket.hora_actualizacion}" #! Mensaje
            )
        else:
            await update.message.reply_text("❌ Ticket no encontrado") #! Mensaje
            return ConversationHandler.END
    except:
        await update.message.reply_text("❌ ID inválido")
        return ConversationHandler.END                #! Mensaje

    return ConversationHandler.END

#!______________________cerrar_____________________________________
async def cerrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    # Verificar si es TI
    if not es_ti(chat_id):
        await update.message.reply_text("❌ Sin permisos")
        return

    try:
        ticket_id = int(context.args[0])

        db = SessionLocal()
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

        if not ticket:
            db.close()
            await update.message.reply_text("❌ Ticket no encontrado")
            return

        # Actualizar estado
        ticket.estado = "Cerrado"

        ahora = datetime.now()
        ticket.fecha_actualizacion = ahora.strftime("%d-%m-%Y")
        ticket.hora_actualizacion = ahora.strftime("%H:%M:%S")

        db.commit()
        chat_usuario = int(ticket.chat_id)
        db.close()

        await update.message.reply_text(f"✅ Ticket #{ticket_id} cerrado")

        # Notificar al usuario
        await context.bot.send_message(
            chat_usuario,
            f"🎉 Tu ticket #{ticket_id} ha sido resuelto"
        )

    except:
        await update.message.reply_text("Uso: /cerrar ID")

#!___________________________________________________________
#! __________________APP__________________
#!___________________________________________________________
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(botones)],
    states={
        AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_area)],
        DESCRIPCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_descripcion)],
        ESTADO_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ver_estado)],
    },
    fallbacks=[],
    per_message=False
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)
app.add_handler(CommandHandler("cerrar", cerrar))

# ! En caso de que no se ejecute /start
async def saludo_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if es_ti(chat_id):
        keyboard = [
            [InlineKeyboardButton("📋 Ver Tickets", callback_data="ver_tickets")],
            [InlineKeyboardButton("🔧 En Proceso", callback_data="en_proceso")],
            
        ]
        mensaje = "<b>Panel TI 👨‍💻</b>\nSelecciona una opción:"
    else:
        keyboard = [
            [InlineKeyboardButton("🎫 Crear Ticket", callback_data="crear")],
            [InlineKeyboardButton("📄 Ver Estado", callback_data="estado")]
        ]
        mensaje = "<b>Hola!</b> 👋\n¿En qué puedo ayudarte?"

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, parse_mode='HTML', reply_markup=reply_markup)

saludo_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, saludo_global)
app.add_handler(saludo_handler)

app.run_polling()