from app.database.connection import db

class PokemonDBController:
    def __init__(self):
        self.db = db

    def crear_tabla(self):
        """
        Crea la estructura solo si NO existe. No borra datos.
        """
        sql = """
            CREATE TABLE IF NOT EXISTS pokemons (
                id INTEGER PRIMARY KEY,
                nombre TEXT,
                imagen TEXT,
                tipos TEXT,
                habilidades TEXT,
                movimientos TEXT,
                generacion TEXT,
                hp INTEGER,
                ataque INTEGER,
                ataque_especial INTEGER,
                defensa INTEGER,
                defensa_especial INTEGER,
                velocidad INTEGER
            );
        """
        try:
            self.db.update(sql)
            return True
        except Exception as e:
            print(f"[DB Error] Creando tabla: {e}")
            return False

    def reiniciar_tabla(self):
        """
        MÉTODO DESTRUCTIVO: Borra la tabla y la vuelve a crear.
        Se usa solo si detectamos que la base de datos está corrupta o incompleta.
        """
        try:
            print("--- Reiniciando tabla Pokemons (DROP & CREATE) ---")
            self.db.update("DROP TABLE IF EXISTS pokemons")
            return self.crear_tabla()
        except Exception as e:
            print(f"[DB Error] Reiniciando tabla: {e}")
            return False

    def contar_registros(self):
        """
        Devuelve el número exacto de pokémons en la BD.
        """
        sql = "SELECT COUNT(*) FROM pokemons"
        try:
            rows = self.db.select(sql)
            # rows[0][0] contiene el número
            return rows[0][0]
        except Exception:
            # Si da error (ej: la tabla no existe), retornamos 0
            return 0

    def guardar_pokemon(self, datos):
        sql = """
            INSERT OR REPLACE INTO pokemons (
                id, nombre, imagen, tipos, habilidades, movimientos, generacion,
                hp, ataque, ataque_especial, defensa, defensa_especial, velocidad
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            datos['id'],
            datos['nombre'],
            datos['imagen'],
            datos['tipos'],
            datos['habilidades'],
            datos['movimientos'],
            datos['generacion'],
            datos['hp'],
            datos['ataque'],
            datos['ataque_especial'],
            datos['defensa'],
            datos['defensa_especial'],
            datos['velocidad']
        )
        try:
            self.db.insert(sql, params)
            return True
        except Exception as e:
            print(f"[DB Error] Al guardar {datos['nombre']}: {e}")
            return False

    # (Mantén el método obtener_todos igual que antes)
    def obtener_todos(self):
        sql = "SELECT * FROM pokemons"
        try:
            rows = self.db.select(sql)
            pokemons = []
            for row in rows:
                pokemons.append({
                    "id": row[0],
                    "nombre": row[1],
                    "imagen": row[2],
                    "tipos": row[3],
                    # ... resto de campos si los necesitas ...
                })
            return pokemons
        except Exception:
            return []