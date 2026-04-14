from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ! Menus
def menu_ti():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Ver Tickets", callback_data="ver_tickets")],
        [InlineKeyboardButton("🔧 En Proceso", callback_data="en_proceso")],
        [InlineKeyboardButton("📊 Reportes", callback_data="reporte")]
    ])
#!---------------------------------------------------------

def menu_usuario():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎫 Crear Ticket", callback_data="crear")],
        [InlineKeyboardButton("📄 Ver Estado", callback_data="estado")]
    ])
#!---------------------------------------------------------

def teclado_tickets(tickets):
    keyboard = []

    for t in tickets:
        keyboard.append([
            InlineKeyboardButton(
                f"#{t.id} | {t.area} | {t.descripcion[:20]}...",
                callback_data=f"ticket_{t.id}"
            )
        ])

    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)
#!---------------------------------------------------------

def teclado_ticket_detalle(ticket_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔧 Tomar", callback_data=f"tomar_{ticket_id}")],
        [InlineKeyboardButton("✅ Cerrar", callback_data=f"cerrar_{ticket_id}")],
        [InlineKeyboardButton("🔙 Volver", callback_data="ver_tickets")]
    ])

def teclado_detalle_proceso(ticket_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Cerrar", callback_data=f"cerrar_{ticket_id}")],
        [InlineKeyboardButton("🔙 Volver", callback_data="en_proceso")]
    ])
#!---------------------------------------------------------

def teclado_reportes():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Todos", callback_data="rep_todos")],
        [InlineKeyboardButton("👨‍💻 Por Asignado TI", callback_data="rep_asig")],
        [InlineKeyboardButton("👤 Por Usuario", callback_data="rep_user")],
        [InlineKeyboardButton("⏱️ Por Periodo", callback_data="periodo")],
        [InlineKeyboardButton("🔙 Volver", callback_data="menu")]
    ])

def teclado_periodo():
    return InlineKeyboardMarkup([
    [InlineKeyboardButton("🌱 Hoy", callback_data="rep_hoy")],
    [InlineKeyboardButton("🌿 Ultimos 7 dias", callback_data="rep_sem")],
    [InlineKeyboardButton("🌳 Ultimos 30 dias", callback_data="rep_mes")],
    [InlineKeyboardButton("🍎 Ultimos 12 meses", callback_data="rep_anyo")],
    [InlineKeyboardButton("📅 Periodo Especifico", callback_data="rep_per")],
    [InlineKeyboardButton("🔙 Volver", callback_data="reporte")]
    ])


# !---------------------------------------------------------
def boton_volver():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Volver al inicio", callback_data="menu")]
    ])
def boton_volver_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Volver al inicio", callback_data="menu_message")]
    ])