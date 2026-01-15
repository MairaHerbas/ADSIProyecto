from datetime import datetime
from app.database.connection import db

class Pokemon:
    @staticmethod
    def get_all():
        """Obtiene todos los pokemons para la caja (disponibles)"""
        sql = "SELECT * FROM pokemons"
        return db.select(sql)

class Equipo:
    def __init__(self, id, user_id, nombre_equipo, created_at):
        self.id = id
        self.user_id = user_id
        self.nombre_equipo = nombre_equipo
        self.created_at = created_at

    @staticmethod
    def get_by_user(user_id):
        # Nodo 4.1 del Diagrama de Consulta
        sql = "SELECT * FROM equipo WHERE user_id = ? ORDER BY created_at DESC"
        rows = db.select(sql, (user_id,))
        return [dict(row) for row in rows] # Convertimos Row a dict

    @staticmethod
    def get_by_id(equipo_id):
        # Nodo 4.1 del Diagrama de Edición
        sql = "SELECT * FROM equipo WHERE id = ?"
        rows = db.select(sql, (equipo_id,))
        if rows:
            return dict(rows[0])
        return None

    @staticmethod
    def create(user_id, nombre):
        # Nodo 3.1.1 del Diagrama de Creación
        sql = "INSERT INTO equipo (user_id, nombre_equipo, created_at) VALUES (?, ?, ?)"
        # Retorna el ID generado (Nodo 3.1.4)
        return db.insert(sql, (user_id, nombre, datetime.utcnow()))

    @staticmethod
    def update(equipo_id, nombre):
        # Nodo 5.1.1 del Diagrama de Edición
        sql = "UPDATE equipo SET nombre_equipo = ? WHERE id = ?"
        db.update(sql, (nombre, equipo_id))

    @staticmethod
    def delete(equipo_id):
        # SQL con borrado en cascada manual (si SQLite no lo tiene activo)
        db.delete("DELETE FROM pokemon_equipo WHERE equipo_id = ?", (equipo_id,))
        db.delete("DELETE FROM equipo WHERE id = ?", (equipo_id,))

    @staticmethod
    def get_members(equipo_id):
        # Obtiene los miembros completos haciendo JOIN con la tabla pokemons
        sql = """
            SELECT pe.*, p.nombre, p.tipos, p.imagen_url 
            FROM pokemon_equipo pe
            JOIN pokemons p ON pe.pokemon_id = p.id
            WHERE pe.equipo_id = ?
            ORDER BY pe.orden ASC
        """
        rows = db.select(sql, (equipo_id,))
        return [dict(row) for row in rows]

class PokemonEquipo:
    @staticmethod
    def create(equipo_id, pokemon_id, orden):
        # Nodo 5.1.3 del Diagrama de Edición
        sql = """
            INSERT INTO pokemon_equipo (equipo_id, pokemon_id, orden, fecha_captura) 
            VALUES (?, ?, ?, ?)
        """
        db.insert(sql, (equipo_id, pokemon_id, orden, datetime.utcnow()))

    @staticmethod
    def delete_by_equipo(equipo_id):
        # Nodo 5.1.2 del Diagrama de Edición
        sql = "DELETE FROM pokemon_equipo WHERE equipo_id = ?"
        db.delete(sql, (equipo_id,))