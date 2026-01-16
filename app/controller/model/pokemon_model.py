from datetime import datetime
from app.database.connection import db

class Pokemon:
    @staticmethod
    def get_all():
        """Obtiene todos los pokemons para la caja (disponibles)"""
        sql = "SELECT * FROM pokemons"
        return db.select(sql)
