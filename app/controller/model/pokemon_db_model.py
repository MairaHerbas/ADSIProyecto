from app.database.connection import db
from app.services.gestor_eventos import GestorEventos

class PokemonDBController:
    def __init__(self):
        self.db = db

    def crear_tabla(self):
        # 1. Tabla de Pokémon
        sql_poke = """
            CREATE TABLE IF NOT EXISTS pokemons (
                id INTEGER PRIMARY KEY,
                nombre TEXT, imagen TEXT, tipos TEXT,
                habilidades TEXT, movimientos TEXT, generacion TEXT,
                hp INTEGER, ataque INTEGER, ataque_especial INTEGER,
                defensa INTEGER, defensa_especial INTEGER, velocidad INTEGER
            );
        """
        # 2. Tabla de Capturas (Relación Usuario <-> Pokémon)
        sql_cap = """
            CREATE TABLE IF NOT EXISTS capturas (
                user_id INTEGER,
                pokemon_id INTEGER,
                fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, pokemon_id)
            );
        """
        try:
            self.db.update(sql_poke)
            self.db.update(sql_cap)
            return True
        except Exception as e:
            print(f"[DB] Error creando tablas: {e}")
            return False

    def reiniciar_tabla(self):
        try:
            self.db.update("DROP TABLE IF EXISTS pokemons")
            self.db.update("DROP TABLE IF EXISTS capturas")
            return self.crear_tabla()
        except Exception as e:
            print(f"[DB Error] Reiniciando tabla: {e}")
            return False

    def guardar_pokemon(self, d):
        sql = "INSERT OR REPLACE INTO pokemons (id, nombre, imagen, tipos, habilidades, movimientos, generacion, hp, ataque, ataque_especial, defensa, defensa_especial, velocidad) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        try:
            self.db.insert(sql, (d['id'], d['nombre'], d['imagen'], d['tipos'], d['habilidades'], d['movimientos'], d['generacion'], d['hp'], d['ataque'], d['ataque_especial'], d['defensa'], d['defensa_especial'], d['velocidad']))
            return True
        except: return False

    def obtener_todos(self):
        sql = "SELECT * FROM pokemons"
        try:
            rows = self.db.select(sql)
            return [{
                "id": r[0], "nombre": r[1], "imagen": r[2], "tipos": r[3],
                "habilidades": r[4], "movimientos": r[5], "generacion": r[6],
                "hp": r[7], "ataque": r[8], "ataque_especial": r[9],
                "defensa": r[10], "defensa_especial": r[11], "velocidad": r[12]
            } for r in rows]
        except: return []

    def contar_registros(self):
        try: return self.db.select("SELECT COUNT(*) FROM pokemons")[0][0]
        except: return 0

    # --- MÉTODOS DE CAPTURA ---

    def obtener_capturados(self, user_id):
        """Devuelve un conjunto (Set) con los IDs capturados por el usuario"""
        try:
            rows = self.db.select("SELECT pokemon_id FROM capturas WHERE user_id = ?", (user_id,))
            return {row[0] for row in rows}
        except: return set()

    def toggle_captura(self, user_id, pokemon_id):
        try:
            # Comprobar si ya existe
            exists = self.db.select("SELECT 1 FROM capturas WHERE user_id = ? AND pokemon_id = ?",
                                    (user_id, pokemon_id))

            if exists:
                # Si existe, lo borramos (LIBERAR)
                self.db.delete("DELETE FROM capturas WHERE user_id = ? AND pokemon_id = ?", (user_id, pokemon_id))
                # 3. CREAR NOTIFICACIÓN
                # Primero obtenemos el nombre para que el mensaje quede bien
                res_nombre = self.db.select("SELECT nombre FROM pokemons WHERE id = ?", (pokemon_id,))
                nombre_poke = res_nombre[0][0] if res_nombre else "Pokémon"

                # Llamamos al gestor usando el método estático
                GestorEventos.registrarEvento(
                    idUsuario=user_id,
                    tipoEvento="Captura",
                    descripcion=f"Ha Liberado a {nombre_poke}"
                )
                return False
            else:
                # Si no existe, lo insertamos (CAPTURAR)
                self.db.insert("INSERT INTO capturas (user_id, pokemon_id) VALUES (?, ?)", (user_id, pokemon_id))

                # 3. CREAR NOTIFICACIÓN
                # Primero obtenemos el nombre para que el mensaje quede bien
                res_nombre = self.db.select("SELECT nombre FROM pokemons WHERE id = ?", (pokemon_id,))
                nombre_poke = res_nombre[0][0] if res_nombre else "Pokémon"

                # Llamamos al gestor usando el método estático
                GestorEventos.registrarEvento(
                    idUsuario=user_id,
                    tipoEvento="Captura",
                    descripcion=f"Ha capturado a {nombre_poke}"
                )

                return True

        except Exception as e:
            print(f"[DB] Error toggle: {e}")
            return False