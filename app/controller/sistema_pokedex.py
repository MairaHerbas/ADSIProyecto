from app.services.gestor_eventos import GestorEventos

class SistemaPokedex:
    
    @staticmethod
    def cargarNotificaciones(usuario):
        return GestorEventos.obtenerNotificaciones(usuario)

    @staticmethod
    def registrarAccion(id_usuario, tipo, descripcion):
        GestorEventos.registrarEvento(id_usuario, tipo, descripcion)