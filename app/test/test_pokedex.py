import unittest
import json
import sys
import os
import time

# --- CONFIGURACIÓN DE RUTAS ---
# Añadimos la raíz del proyecto al path para poder importar 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import session
from app.database.connection import db
from run import app  # Importamos la app principal


class TestPlanPokedex(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """CONFIGURACIÓN PREVIA: Se ejecuta una vez antes de todas las pruebas"""
        print("\n" + "=" * 60)
        print(" EJECUTANDO PLAN DE PRUEBAS AUTOMATIZADO (Backend Support)")
        print(" Basado en documentación: Casos de Uso 'Consultar Pokedex'")
        print("=" * 60)

        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        cls.client = app.test_client()

        # Aseguramos que la DB tenga las tablas creadas
        from app.controller.model.pokemon_db_model import PokemonDBController
        db_ctrl = PokemonDBController()
        db_ctrl.crear_tabla()

        # Usuario de prueba ID 999
        cls.test_user_id = 999

    def setUp(self):
        # Simulamos sesión para cada prueba
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.test_user_id


    def test_CP_API_LIST_01_Carga_Inicial(self):
        """
        [CP-API-LIST-01] Carga Inicial API
        Verifica que el endpoint /api/pokedex devuelve una lista válida y ordenada.
        """
        print("\n[CP-API-LIST-01] Probando Carga Inicial API...")
        response = self.client.get('/api/pokedex')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertTrue(len(data) > 0, "La lista debería contener Pokémon")

        # Verificamos orden y datos básicos del primero (Bulbasaur #1)
        first = data[0]
        self.assertEqual(first['id'], 1, "El primer Pokémon debería ser ID 1")
        self.assertIn('name', first)
        self.assertIn('sprite', first)
        print("   -> OK: Lista cargada y estructura básica correcta.")

    def test_CP_API_LIST_02_Paginacion(self):
        """
        [CP-API-LIST-02] Paginación/Scroll
        NOTA: En la implementación actual (v1.0), el backend envía TODA la lista (1000+).
        La paginación es visual (JS). Este test verifica que el backend envía
        suficientes datos para que el JS haga scroll infinito.
        """
        print("\n[CP-API-LIST-02] Validando Datos para Scroll/Paginación...")
        response = self.client.get('/api/pokedex')
        data = response.get_json()

        # Si recibimos más de 50 items, el backend cumple su parte para el scroll del frontend
        self.assertTrue(len(data) > 50, "El backend debe enviar suficientes datos para permitir scroll")
        print(f"   -> OK: Se recibieron {len(data)} registros (Backend OK). UI debe gestionar el scroll.")

    def test_CP_API_LIST_04_Rendimiento(self):
        """
        [CP-API-LIST-04] Rendimiento (Prueba de Estrés Básica)
        Simula 5 peticiones seguidas.
        """
        print("\n[CP-API-LIST-04] Prueba de Estrés (5 peticiones)...")
        start_time = time.time()
        for i in range(5):
            rv = self.client.get('/api/pokedex')
            self.assertEqual(rv.status_code, 200)
        duration = time.time() - start_time
        print(f"   -> OK: 5 peticiones completadas en {duration:.2f} segundos.")

    # CP-API-LIST-03 (Sin Conexión) y CP-API-UI-01 (Navegación)
    # requieren pruebas manuales o desconectar el cable de red, no se pueden automatizar aquí.

    # =========================================================================
    # SECCIÓN 4.2: FILTROS DE BÚSQUEDA
    # NOTA: El filtrado es JS. Aquí testeamos que los DATOS soportan el filtrado.
    # =========================================================================

    def test_CP_FIL_Support_Data(self):
        """
        [CP-FIL-01 a 06] Validación de Datos para Filtros
        Simula la lógica del JS para asegurar que la API manda los datos necesarios.
        """
        print("\n[CP-FIL-XX] Validando integridad de datos para filtros JS...")
        response = self.client.get('/api/pokedex')
        data = response.get_json()

        # [CP-FIL-01] Filtro por Nombre (Simulación)
        # Buscamos "cha"
        filtered_name = [p for p in data if "cha" in p['name'].lower()]
        self.assertTrue(len(filtered_name) > 0, "Deberían existir Pokémon con 'cha'")
        print("   -> OK: Datos soportan filtro por nombre (CP-FIL-01)")

        # [CP-FIL-03] Filtro por Tipo (Simulación)
        # Buscamos tipo "fire"
        filtered_type = [p for p in data if "fire" in p['types']]
        self.assertTrue(len(filtered_type) > 0, "Deberían existir Pokémon tipo 'fire'")
        print("   -> OK: Datos soportan filtro por tipo (CP-FIL-03)")

        # [CP-FIL-05] Filtros Combinados (Simulación)
        # Nombre "char" Y Tipo "fire"
        filtered_combo = [p for p in data if "char" in p['name'].lower() and "fire" in p['types']]
        self.assertTrue(len(filtered_combo) > 0, "Debería existir Charizard/Charmeleon")
        print("   -> OK: Datos soportan filtros combinados (CP-FIL-05)")

        # [CP-FIL-02] y [CP-FIL-06] (Casos vacíos)
        # Simplemente verificamos que el filtro devuelve 0 sin romper el código python
        none_list = [p for p in data if "xyz123" in p['name']]
        self.assertEqual(len(none_list), 0)
        print("   -> OK: Filtrado negativo gestionado correctamente.")

    # =========================================================================
    # SECCIÓN 4.3: VER DETALLES DE POKÉMON
    # =========================================================================

    def test_CP_DET_01_Integridad_Detalles(self):
        """
        [CP-DET-01] y [CP-DET-03] Integridad de Datos
        Verifica que al pedir la lista, los objetos tienen los detalles completos
        que se mostrarán en la modal.
        """
        print("\n[CP-DET-01/03] Verificando detalles completos (Stats, Habilidades)...")
        response = self.client.get('/api/pokedex')
        data = response.get_json()

        # Buscamos un Pokémon conocido (ej: Charizard) para validar integridad
        target = next((p for p in data if p['name'] == 'charizard'), None)
        self.assertIsNotNone(target, "Charizard debería existir")

        # Verificamos campos críticos para la vista detalle
        self.assertIn('stats', target)
        self.assertTrue(target['stats']['hp'] > 0)

        self.assertIn('habilidades', target)
        self.assertIsInstance(target['habilidades'], str)  # Debe ser string para que el JS haga split

        self.assertIn('movimientos', target)

        print("   -> OK: Los datos de detalle (Stats, Moves, Habilidades) son correctos.")

    def test_CP_DET_04_Datos_Incompletos(self):
        """
        [CP-DET-04] Datos Incompletos (API)
        Verifica que ningún Pokémon rompa la estructura (ej: stats null).
        """
        print("\n[CP-DET-04] Validando consistencia de datos (No Nulls)...")
        response = self.client.get('/api/pokedex')
        data = response.get_json()

        for p in data[:50]:  # Revisamos los primeros 50 para no tardar mucho
            self.assertIsNotNone(p['name'])
            self.assertIsNotNone(p['types'])
            self.assertIsNotNone(p['stats'])
            # Aseguramos que la lista de tipos no esté vacía (o sea 'unknown')
            self.assertTrue(len(p['types']) > 0)

        print("   -> OK: Muestreo de datos validado sin valores nulos críticos.")

    # [CP-DET-02] Acceso desde Equipo: Requiere módulo de equipos (no incluido aquí).
    # [CP-DET-05/06] UI/Red: Pruebas manuales.

    @classmethod
    def tearDownClass(cls):
        print("\n" + "=" * 60)
        print(" FIN DE PRUEBAS AUTOMATIZADAS")
        print("=" * 60)


if __name__ == '__main__':
    unittest.main()