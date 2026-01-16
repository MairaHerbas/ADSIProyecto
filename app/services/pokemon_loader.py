# En app/services/pokemon_loader.py
import os
import sqlite3
import requests

# Ajuste de ruta: subir 3 niveles (services -> app -> root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "instance", "pokedex.db")

class PokemonLoader:
    # ... (EL RESTO DE TU CÓDIGO PERMANECE IGUAL) ...
    # Asegúrate de que tu métodOo _conectar use os.makedirs para crear la carpeta instance si no existe
    def __init__(self):
        self.api_url = "https://pokeapi.co/api/v2/pokemon/"

    def _conectar(self):
        directorio = os.path.dirname(DB_PATH)


        if directorio and not os.path.exists(directorio):
            try:
                os.makedirs(directorio)
                print(f"Directorio creado: {directorio}")
            except OSError as e:
                print(f"Error al crear el directorio: {e}")
                raise



        conn = sqlite3.connect(DB_PATH)
        return conn

    def inicializar_db(self):
        conn = self._conectar()
        cursor = conn.cursor()
        # IMPORTANTE: Definimos las 13 columnas exactas que luego insertamos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokemons (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                imagen_url TEXT,
                generacion INTEGER,
                altura REAL,
                peso REAL,
                tipos TEXT,
                habilidades TEXT,
                movimientos TEXT,
                hp INTEGER,
                ataque INTEGER,
                defensa INTEGER,
                velocidad INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def db_esta_vacia(self):
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM pokemons")
            cantidad = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            return True
        conn.close()
        return cantidad == 0

    def descargar_datos(self, limite=386):
        print(f"⚡ Iniciando descarga de {limite} Pokemons...")
        conn = self._conectar()
        cursor = conn.cursor()
        session = requests.Session()

        for i in range(1, limite + 1):
            try:
                res = session.get(f"{self.api_url}{i}")
                if res.status_code == 200:
                    data = res.json()
                    nombre = data['name'].capitalize()

                    # Imagen HD
                    img = data['sprites']['other']['official-artwork']['front_default'] or data['sprites'][
                        'front_default']

                    # Generación (simplificada)
                    gen = 1
                    if i > 151: gen = 2
                    if i > 251: gen = 3

                    # Listas a Texto
                    tipos = ", ".join([t['type']['name'].capitalize() for t in data['types']])
                    habs = ", ".join([a['ability']['name'].replace('-', ' ').capitalize() for a in data['abilities']])
                    movs = ", ".join(
                        [m['move']['name'].replace('-', ' ').capitalize() for m in data['moves'][:8]])  # Solo 8 movs

                    # Stats
                    stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}

                    cursor.execute('''
                        INSERT OR REPLACE INTO pokemons VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (i, nombre, img, gen, data['height'] / 10, data['weight'] / 10, tipos, habs, movs,
                          stats.get('hp', 0), stats.get('attack', 0), stats.get('defense', 0), stats.get('speed', 0)))

                    if i % 20 == 0: print(f"   ...Guardado ID {i}")
            except Exception as e:
                print(f"Error en {i}: {e}")

        conn.commit()
        conn.close()
        print(" Base de datos lista.")

    def buscar_pokemons(self, nombre="", tipo="", generacion=""):
        conn = self._conectar()
        cursor = conn.cursor()
        query = "SELECT * FROM pokemons WHERE 1=1"
        params = []

        if nombre:
            query += " AND nombre LIKE ?"
            params.append(f"%{nombre}%")
        if tipo:
            query += " AND tipos LIKE ?"
            params.append(f"%{tipo}%")
        if generacion:
            query += " AND generacion = ?"
            params.append(generacion)

        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_por_id(self, id_poke):
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pokemons WHERE id = ?", (id_poke,))
        data = cursor.fetchone()
        conn.close()
        return data