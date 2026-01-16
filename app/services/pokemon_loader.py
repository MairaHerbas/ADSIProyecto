import requests
from app.controller.model.pokemon_db_controller import PokemonDBController


class PokemonLoader:
    def __init__(self):
        self.db_controller = PokemonDBController()
        # Límite de la API (Actualmente hay 1025 pokemons + formas)
        self.TOTAL_POKEMONS_OBJETIVO = 1025
        self.api_url = f"https://pokeapi.co/api/v2/pokemon?limit={self.TOTAL_POKEMONS_OBJETIVO}&offset=0"

    def descargar_datos(self):
        """
        Lógica Inteligente:
        1. Asegura que la tabla existe.
        2. Cuenta cuántos tenemos.
        3. Si tenemos los 1025 -> NO HACE NADA (Arranque rápido).
        4. Si faltan -> BORRA TODO y descarga de cero (Para evitar duplicados o errores).
        """
        # Paso 1: Asegurar estructura (sin borrar nada aun)
        self.db_controller.crear_tabla()

        # Paso 2: Contar
        cantidad_actual = self.db_controller.contar_registros()
        print(f"--- Verificando Base de Datos: Hay {cantidad_actual} / {self.TOTAL_POKEMONS_OBJETIVO} Pokémon ---")

        if cantidad_actual >= self.TOTAL_POKEMONS_OBJETIVO:
            print("✅ La Base de Datos ya está completa. Omitiendo descarga.")
            return True

        # Paso 3: Si no coincide (ej: está vacía o a medias), reiniciamos
        if cantidad_actual > 0:
            print("⚠️ La base de datos parece incompleta. Se reiniciará la carga.")

        # Borramos tabla y creamos de nuevo para empezar limpio
        self.db_controller.reiniciar_tabla()
        return self.importar_datos_api()

    def get_generacion(self, poke_id):
        if poke_id <= 151: return "Gen 1"
        if poke_id <= 251: return "Gen 2"
        if poke_id <= 386: return "Gen 3"
        if poke_id <= 493: return "Gen 4"
        if poke_id <= 649: return "Gen 5"
        if poke_id <= 721: return "Gen 6"
        if poke_id <= 809: return "Gen 7"
        if poke_id <= 905: return "Gen 8"
        return "Gen 9"

    def importar_datos_api(self):
        print(f"--- Iniciando DESCARGA MASIVA de {self.TOTAL_POKEMONS_OBJETIVO} Pokémons... ---")
        try:
            response = requests.get(self.api_url)
            data = response.json()
            results = data.get('results', [])
            total = len(results)

            count = 0
            # Usamos session para mejorar velocidad de conexión
            with requests.Session() as session:
                for item in results:
                    try:
                        r_detalle = session.get(item['url'])
                        detalles = r_detalle.json()

                        poke_id = detalles['id']

                        # Mapeo de datos (Stats, Tipos, Movimientos)
                        tipos = ",".join([t['type']['name'] for t in detalles['types']])
                        habilidades = ",".join([a['ability']['name'] for a in detalles['abilities']])
                        # Limitamos a los primeros 20 movimientos para no saturar la BD con texto innecesario
                        # o guardamos todos si prefieres. Aquí guardo todos:
                        movimientos = ",".join([m['move']['name'] for m in detalles['moves']])

                        stats = {s['stat']['name']: s['base_stat'] for s in detalles['stats']}

                        datos_pokemon = {
                            "id": poke_id,
                            "nombre": detalles['name'],
                            "imagen": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke_id}.png",
                            "tipos": tipos,
                            "habilidades": habilidades,
                            "movimientos": movimientos,
                            "generacion": self.get_generacion(poke_id),
                            "hp": stats.get('hp', 0),
                            "ataque": stats.get('attack', 0),
                            "defensa": stats.get('defense', 0),
                            "ataque_especial": stats.get('special-attack', 0),
                            "defensa_especial": stats.get('special-defense', 0),
                            "velocidad": stats.get('speed', 0)
                        }

                        self.db_controller.guardar_pokemon(datos_pokemon)
                        count += 1

                        if count % 50 == 0:
                            print(f"Guardando... {count}/{total}")

                    except Exception as e_interno:
                        print(f"Error en ID {poke_id}: {e_interno}")

            print(f"--- ¡ÉXITO! {count} pokémons guardados ---")
            return True

        except Exception as e:
            print(f"Error CRÍTICO en loader: {e}")
            return False