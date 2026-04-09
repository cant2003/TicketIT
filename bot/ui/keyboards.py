from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ! Menus
def menu_ti():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Ver Tickets", callback_data="ver_tickets")],
        [InlineKeyboardButton("🔧 En Proceso", callback_data="en_proceso")],
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
#!---------------------------------------------------------

