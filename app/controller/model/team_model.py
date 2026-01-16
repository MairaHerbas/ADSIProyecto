# app/controller/model/team_model.py
from datetime import datetime
from app.database.connection import db


class Equipo:
    def __init__(self, id, user_id, nombre_equipo, created_at):
        self.id = id
        self.user_id = user_id
        self.nombre_equipo = nombre_equipo
        self.created_at = created_at

    @staticmethod
    def get_by_user(user_id):
        sql = "SELECT * FROM equipo WHERE user_id = ? ORDER BY created_at DESC"
        rows = db.select(sql, (user_id,))
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(equipo_id):
        sql = "SELECT * FROM equipo WHERE id = ?"
        rows = db.select(sql, (equipo_id,))
        if rows:
            return dict(rows[0])
        return None

    @staticmethod
    def create(user_id, nombre):
        sql = "INSERT INTO equipo (user_id, nombre_equipo, created_at) VALUES (?, ?, ?)"
        return db.insert(sql, (user_id, nombre, datetime.utcnow()))

    @staticmethod
    def update(equipo_id, nombre):
        sql = "UPDATE equipo SET nombre_equipo = ? WHERE id = ?"
        db.update(sql, (nombre, equipo_id))

    @staticmethod
    def delete(equipo_id):
        db.delete("DELETE FROM pokemon_equipo WHERE equipo_id = ?", (equipo_id,))
        db.delete("DELETE FROM equipo WHERE id = ?", (equipo_id,))

    @staticmethod
    def get_members(equipo_id):
        # CORRECCIÓN AQUÍ: Se cambió p.imagen_url por p.imagen
        sql = """
            SELECT pe.*, p.nombre, p.tipos, p.imagen 
            FROM pokemon_equipo pe
            JOIN pokemons p ON pe.pokemon_id = p.id
            WHERE pe.equipo_id = ?
            ORDER BY pe.orden ASC
        """
        rows = db.select(sql, (equipo_id,))

        # Mapeamos 'imagen' a 'sprite' o 'imagen_url' si el front lo espera así,
        # pero el SQL debe usar el nombre real de la columna.
        results = []
        for row in rows:
            d = dict(row)
            # Para evitar errores en el front si espera imagen_url, se lo asignamos manual
            d['imagen_url'] = d['imagen']
            results.append(d)
        return results


class PokemonEquipo:
    @staticmethod
    def create(equipo_id, pokemon_id, orden):
        sql = """
            INSERT INTO pokemon_equipo (equipo_id, pokemon_id, orden, fecha_captura) 
            VALUES (?, ?, ?, ?)
        """
        db.insert(sql, (equipo_id, pokemon_id, orden, datetime.utcnow()))

    @staticmethod
    def delete_by_equipo(equipo_id):
        sql = "DELETE FROM pokemon_equipo WHERE equipo_id = ?"
        db.delete(sql, (equipo_id,))

    @staticmethod
    def delete_one(equipo_id, pokemon_id):
        sql = "DELETE FROM pokemon_equipo WHERE equipo_id = ? AND pokemon_id = ?"
        db.delete(sql, (equipo_id, pokemon_id))