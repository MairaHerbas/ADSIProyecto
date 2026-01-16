import unittest
from unittest.mock import patch
from app import create_app
from app.database.connection import db

# Importamos tu controlador
from app.controller.model.pokemon_db_controller import PokemonDBController

class TestGestionEquipos(unittest.TestCase):

    def setUp(self):
        # 1. BLOQUEAR LA DESCARGA DE LA API (MOCK)
        # Esto evita que 'create_app' descargue datos reales, sin tener que tocar __init__.py
        self.loader_patcher = patch('app.services.pokemon_loader.PokemonLoader.descargar_datos')
        self.mock_loader = self.loader_patcher.start()

        # 2. Iniciar App
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # 3. Preparar Base de Datos con tu Controlador
        with self.app.app_context():
            # Limpiar tablas primero
            db.update("DELETE FROM pokemon_equipo", ())
            db.update("DELETE FROM equipo", ())
            db.update("DELETE FROM user", ())
            db.update("DELETE FROM pokemons", ())

            # Usar tu controlador para asegurar tablas y crear datos
            poke_ctrl = PokemonDBController()
            poke_ctrl.crear_tabla() # Asegura que existen pokemons y capturas

            # Insertar Pokémons de prueba usando TU función guardar_pokemon
            for i in range(1, 101):
                # Creamos el diccionario que espera tu función
                data_poke = {
                    "id": i,
                    "nombre": f"Pokemon {i}",
                    "imagen": f"sprite_{i}.png",
                    "tipos": "Normal",
                    "habilidades": "Ninguna",
                    "movimientos": "Placaje",
                    "generacion": "1",
                    "hp": 50, "ataque": 50, "ataque_especial": 50,
                    "defensa": 50, "defensa_especial": 50, "velocidad": 50
                }
                poke_ctrl.guardar_pokemon(data_poke)

            # Crear Usuario de prueba
            db.insert("INSERT INTO user (id, name, username, email, password_hash, role) VALUES (?, ?, ?, ?, ?, ?)",
                      (1, 'Test User', 'testuser', 'test@test.com', '1234', 'user'))

    def tearDown(self):
        # Detener el bloqueo de descarga
        self.loader_patcher.stop()

        # Limpiar datos
        with self.app.app_context():
            db.update("DELETE FROM pokemon_equipo", ())
            db.update("DELETE FROM equipo", ())
            db.update("DELETE FROM user", ())
            # db.update("DELETE FROM pokemons", ())  <-- COMENTADO: Si quieres conservar los datos reales al volver a run.py
            pass

    # ==========================================================================
    # TESTS (Sin cambios en la lógica, solo se benefician de la carga rápida)
    # ==========================================================================

    def test_CP_EQP_01_crear_equipo(self):
        print("\n--- Ejecutando CP-EQP-01: Crear Equipo ---")
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        res = self.client.post('/api/team/init')
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        team_id = data['id']

        # Añadir Pokémon (Usamos los IDs que creamos con el controlador)
        r1 = self.client.post('/api/team/add-member', json={'team_id': team_id, 'pokemon_id': 1})
        r2 = self.client.post('/api/team/add-member', json={'team_id': team_id, 'pokemon_id': 2})

        self.assertTrue(r1.get_json()['success'])
        self.assertTrue(r2.get_json()['success'])

        rows = db.select("SELECT * FROM pokemon_equipo WHERE equipo_id = ?", (team_id,))
        self.assertEqual(len(rows), 2)

    def test_CP_EQP_02_limite_maximo(self):
        print("\n--- Ejecutando CP-EQP-02: Límite Máximo ---")
        with self.client.session_transaction() as sess: sess['user_id'] = 1

        res_init = self.client.post('/api/team/init')
        team_id = res_init.get_json()['id']

        for i in range(1, 7):
            self.client.post('/api/team/add-member', json={'team_id': team_id, 'pokemon_id': i})

        res_fail = self.client.post('/api/team/add-member', json={'team_id': team_id, 'pokemon_id': 7})
        data_fail = res_fail.get_json()

        self.assertFalse(data_fail['success'])
        self.assertIn("lleno", data_fail.get('error', '').lower())

    def test_CP_EQP_08_cambiar_nombre(self):
        print("\n--- Ejecutando CP-EQP-08: Cambiar Nombre ---")
        with self.client.session_transaction() as sess: sess['user_id'] = 1

        res = self.client.post('/api/team/init')
        t_id = res.get_json()['id']

        new_name = "Equipo Maestro"
        self.client.post('/api/team/set-name', json={'id': t_id, 'name': new_name})

        row = db.select("SELECT nombre_equipo FROM equipo WHERE id = ?", (t_id,))
        self.assertEqual(row[0]['nombre_equipo'], new_name)

    def test_CP_EQP_09_eliminar_equipo(self):
        print("\n--- Ejecutando CP-EQP-09: Eliminar Equipo ---")
        with self.client.session_transaction() as sess: sess['user_id'] = 1

        res = self.client.post('/api/team/init')
        t_id = res.get_json()['id']

        res_del = self.client.post('/api/team-delete', json={'id': t_id})
        self.assertTrue(res_del.get_json()['success'])

        check = db.select("SELECT * FROM equipo WHERE id = ?", (t_id,))
        self.assertEqual(len(check), 0)

    def test_CP_EQP_07_quitar_miembro(self):
        print("\n--- Ejecutando CP-EQP-07: Quitar Miembro ---")
        with self.client.session_transaction() as sess: sess['user_id'] = 1
        res = self.client.post('/api/team/init')
        t_id = res.get_json()['id']

        self.client.post('/api/team/add-member', json={'team_id': t_id, 'pokemon_id': 1})
        self.client.post('/api/team/remove-member', json={'team_id': t_id, 'pokemon_id': 1})

        rows_after = db.select("SELECT * FROM pokemon_equipo WHERE equipo_id = ?", (t_id,))
        self.assertEqual(len(rows_after), 0)

if __name__ == '__main__':
    unittest.main()