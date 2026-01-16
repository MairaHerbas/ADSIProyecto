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
        try:
            print("--- Reiniciando tabla Pokemons (DROP & CREATE) ---")
            self.db.update("DROP TABLE IF EXISTS pokemons")
            return self.crear_tabla()
        except Exception as e:
            print(f"[DB Error] Reiniciando tabla: {e}")
            return False

    def contar_registros(self):
        sql = "SELECT COUNT(*) FROM pokemons"
        try:
            rows = self.db.select(sql)
            return rows[0][0]
        except Exception:
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

    # --- AQUÍ ESTABA EL FALLO, AHORA MAPEAMOS TODO ---
    def obtener_todos(self):
        sql = "SELECT * FROM pokemons"
        try:
            rows = self.db.select(sql)
            pokemons = []
            for row in rows:
                # Mapeamos TODAS las columnas por su índice (orden de creación)
                pokemons.append({
                    "id": row[0],
                    "nombre": row[1],
                    "imagen": row[2],
                    "tipos": row[3],
                    "habilidades": row[4],
                    "movimientos": row[5],
                    "generacion": row[6],
                    "hp": row[7],
                    "ataque": row[8],
                    "ataque_especial": row[9],
                    "defensa": row[10],
                    "defensa_especial": row[11],
                    "velocidad": row[12]
                })
            return pokemons
        except Exception as e:
            print(f"Error recuperando pokemons: {e}")
            return []

    def esta_vacia(self):
        return self.contar_registros() == 0