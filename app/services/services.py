# app/services.py
from app.extensions import db
from app.controller.model.models import Event, User


class ChangelogService:

    @staticmethod
    def registrar_evento(user_id, tipo, mensaje):
        """
        Esta función la usarán tus compañeros (Funcionalidad 2) para
        registrar acciones.
        Ejemplo: ChangelogService.registrar_evento(current_user.id, 'EQUIPO', 'Ha creado el equipo Fuego')
        """
        nuevo_evento = Event(user_id=user_id, event_type=tipo, description=mensaje)
        db.session.add(nuevo_evento)
        db.session.commit()

    @staticmethod
    def obtener_feed_amigos(current_user, filtro_usuario=None):
        """
        Obtiene los eventos de los usuarios seguidos (amigos).
        Permite filtrar por un nombre de usuario específico.
        """
        # 1. Obtenemos los IDs de los amigos
        # Según tu modelo actual, friends es una relación bidireccional
        amigos_ids = [amigo.id for amigo in current_user.friends]

        # Incluimos nuestros propios eventos también (opcional, pero común en redes sociales)
        ids_a_buscar = amigos_ids + [current_user.id]

        query = Event.query.filter(Event.user_id.in_(ids_a_buscar))

        # 2. Aplicar filtro si existe 
        if filtro_usuario:
            usuario_filtrado = User.query.filter_by(username=filtro_usuario.strip().lower()).first()
            if usuario_filtrado and usuario_filtrado.id in ids_a_buscar:
                query = query.filter(Event.user_id == usuario_filtrado.id)
            elif usuario_filtrado:
                # Si el usuario existe pero no es amigo, no mostramos nada por privacidad
                return []
            else:
                # Usuario no encontrado
                return []

        # 3. Ordenar por fecha (más reciente primero)
        return query.order_by(Event.created_at.desc()).all()