# app/services/services.py
from app.controller.model.user_model import Event, User


class ChangelogService:

    @staticmethod
    def registrar_evento(user_id, tipo, mensaje):
        """
        Registra una acción en la base de datos usando SQL puro.
        """
        Event.create(user_id, tipo, mensaje)

    @staticmethod
    def obtener_feed_amigos(current_user, filtro_usuario=None):
        """
        Obtiene los eventos de los amigos y del propio usuario.
        Adaptado para SQL puro.
        """
        # 1. Obtener IDs de amigos y el propio
        # (current_user.friends devuelve una lista de objetos User)
        amigos_ids = [amigo.id for amigo in current_user.friends]
        ids_a_buscar = amigos_ids + [current_user.id]

        # 2. Aplicar filtro de usuario si existe
        if filtro_usuario:
            usuario_filtrado = User.get_by_username(filtro_usuario.strip())

            if usuario_filtrado and usuario_filtrado.id in ids_a_buscar:
                # Si existe y es amigo (o yo mismo), buscamos solo sus eventos
                ids_a_buscar = [usuario_filtrado.id]
            else:
                # Usuario no encontrado o no es amigo
                return []

        # 3. Obtener eventos usando la nueva función del modelo
        return Event.get_recent_by_users(ids_a_buscar)