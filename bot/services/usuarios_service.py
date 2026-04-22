from backend.db import Usuario, UsuarioTI, get_db, get_db_tx


def obtener_o_crear_usuario(nombre: str, chat_id: str):
    with get_db_tx() as db:
        usuario = db.query(Usuario).filter(Usuario.chat_id == str(chat_id)).first()

        if usuario:
            if usuario.nombre != nombre:
                usuario.nombre = nombre
                db.flush()
                db.refresh(usuario)
            return usuario

        usuario = Usuario(
            nombre=nombre,
            chat_id=str(chat_id),
        )
        db.add(usuario)
        db.flush()
        db.refresh(usuario)
        return usuario


def obtener_o_crear_usuario_ti(nombre: str, telegram_id: str):
    with get_db_tx() as db:
        usuario_ti = (
            db.query(UsuarioTI)
            .filter(UsuarioTI.telegram_id == str(telegram_id))
            .first()
        )

        if usuario_ti:
            if usuario_ti.nombre != nombre:
                usuario_ti.nombre = nombre
                db.flush()
                db.refresh(usuario_ti)
            return usuario_ti

        usuario_ti = UsuarioTI(
            nombre=nombre,
            telegram_id=str(telegram_id),
        )
        db.add(usuario_ti)
        db.flush()
        db.refresh(usuario_ti)
        return usuario_ti


def es_ti_por_telegram_id(telegram_id):
    with get_db() as db:
        usuario_ti = (
            db.query(UsuarioTI)
            .filter(UsuarioTI.telegram_id == str(telegram_id))
            .first()
        )
        return usuario_ti is not None


def obtener_usuarios_ti():
    with get_db() as db:
        return db.query(UsuarioTI).order_by(UsuarioTI.nombre.asc()).all()


def obtener_telegram_ids_ti():
    with get_db() as db:
        usuarios_ti = db.query(UsuarioTI).all()
        return [usuario.telegram_id for usuario in usuarios_ti]