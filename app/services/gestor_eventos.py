from app.database.connection import db
from app.database.resultado_sql import ResultadoSQL
from app.controller.model.changelog_model import ChangelogEvent

class GestorEventos:
    
    @staticmethod
    def registrarEvento(idUsuario, tipoEvento, descripcion):
        # Implementación del Diagrama 2: Registrar Evento
        # SQL: INSERT INTO Changelog_Event ...
        sql = """
            INSERT INTO Changelog_Event (idUsuario, tipo, descripcion, fecha) 
            VALUES (?, ?, ?, datetime('now', 'localtime'))
        """
        db.insert(sql, (idUsuario, tipoEvento, descripcion))

    @staticmethod
    def obtenerNotificaciones(usuario):
        # Implementación del Diagrama 1: Consultar Notificación
        
        # 1. Obtener lista de IDs (Usuario + Amigos)
        ids_a_buscar = [amigo.id for amigo in usuario.friends]
        ids_a_buscar.append(usuario.id)

        # 2. Generar placeholders dinámicos (?,?,?)
        placeholders = ','.join(['?'] * len(ids_a_buscar))
        
        # 3. Ejecutar SQL
        sql = f"""
            SELECT * FROM Changelog_Event 
            WHERE idUsuario IN ({placeholders}) 
            ORDER BY fecha DESC
        """
        filas_crudas = db.select(sql, tuple(ids_a_buscar))

        # 4. Usar ResultadoSQL para procesar los datos
        resultado = ResultadoSQL(filas_crudas)
        lista_eventos = []

        while resultado.next():
            # Extraemos datos usando getString como pide el diagrama
            id_evt = resultado.getString("id")
            id_usr = resultado.getString("idUsuario")
            tipo = resultado.getString("tipo")
            desc = resultado.getString("descripcion")
            fecha = resultado.getString("fecha")

            nuevo_evento = ChangelogEvent(id_evt, id_usr, tipo, desc, fecha)
            lista_eventos.append(nuevo_evento)

        return lista_eventos