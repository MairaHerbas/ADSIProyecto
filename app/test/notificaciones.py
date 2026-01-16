import unittest
import sys
import os
import sqlite3
from unittest.mock import MagicMock

# =============================================================================
# 1. BLOQUE DE SEGURIDAD TOTAL (MOCKING PREVENTIVO)
# =============================================================================
# Definimos manualmente las librerías que sabemos que dan problemas
# para que Python crea que existen sin tener que instalarlas.

modules_to_mock = [
    'flask', 
    'flask_cors', 
    'werkzeug', 
    'werkzeug.security', 
    'werkzeug.exceptions',
    'requests',       # <--- LA QUE TE ACABA DE FALLAR
    'requests.auth',  # Por si acaso
    'dotenv',         # Común en estos proyectos
    'psycopg2'        # Común si usas Postgres
]

for mod in modules_to_mock:
    sys.modules[mod] = MagicMock()

# =============================================================================
# 2. CONFIGURACIÓN DE RUTAS
# =============================================================================
# Subimos 2 niveles para poder importar 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# =============================================================================
# 3. MOCKS INTERNOS DE LA APP (Modelos y Config)
# =============================================================================

# --- MOCK: ChangelogEvent ---
class MockChangelogEvent:
    def __init__(self, id_evt, id_usr, tipo, desc, fecha):
        self.id = id_evt
        self.idUsuario = id_usr
        self.tipo = tipo
        self.descripcion = desc
        self.fecha = fecha
    
    def __repr__(self):
        return f"Event({self.tipo}: {self.descripcion})"

# Inyectamos el mock del modelo
mock_model = MagicMock()
mock_model.ChangelogEvent = MockChangelogEvent
sys.modules['app.controller.model.changelog_model'] = mock_model

# --- MOCK: Config (Base de datos en memoria) ---
mock_config = MagicMock()
mock_config.Config.DB_PATH = ":memory:" 
sys.modules['config'] = mock_config

# =============================================================================
# 4. IMPORTACIONES REALES
# =============================================================================
try:
    from app.services.gestor_eventos import GestorEventos
    from app.database.connection import db as real_db_instance
except ImportError as e:
    # Si falla aquí, es un error de tu código local, no de librería externa
    print(f"\n❌ Error cargando tu código: {e}")
    print("Asegúrate de ejecutar: python app/test/notificaciones.py desde la RAÍZ.\n")
    sys.exit(1)

# =============================================================================
# 5. TEST SUITE
# =============================================================================

class MockUser:
    """Simula el Usuario y sus amigos"""
    def __init__(self, user_id, friends_list=None):
        self.id = user_id
        self.friends = friends_list if friends_list else []

class TestPlanChangelog(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Prepara la DB en memoria"""
        # Forzamos conexión SQLite en RAM
        real_db_instance.connection = sqlite3.connect(':memory:', check_same_thread=False)
        real_db_instance.connection.row_factory = sqlite3.Row
        
        # Creamos tabla
        cursor = real_db_instance.connection.cursor()
        cursor.execute('''
            CREATE TABLE Changelog_Event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idUsuario TEXT,
                tipo TEXT,
                descripcion TEXT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        real_db_instance.connection.commit()

    def setUp(self):
        """Limpia datos antes de cada test"""
        cursor = real_db_instance.connection.cursor()
        cursor.execute("DELETE FROM Changelog_Event")
        real_db_instance.connection.commit()

    # --- CASOS DE PRUEBA (ADSI-44-45.pdf) ---

    def test_cp_log_gen_01_creacion_equipo(self):
        """ CP-LOG-GEN-01: Notificación Equipo (Creación) """
        usuario_B = MockUser("User_B") 
        usuario_A = MockUser("User_A", friends_list=[usuario_B])
        
        GestorEventos.registrarEvento(usuario_B.id, "EQUIPO_CREADO", "Ha creado el equipo Fuego")
        
        notificaciones = GestorEventos.obtenerNotificaciones(usuario_A)
        
        self.assertTrue(len(notificaciones) > 0, "Fallo: No se generó notificación")
        self.assertEqual(notificaciones[0].idUsuario, "User_B")
        self.assertEqual(notificaciones[0].tipo, "EQUIPO_CREADO")

    def test_cp_log_gen_02_edicion_equipo(self):
        """ CP-LOG-GEN-02: Notificación Equipo (Edición) """
        usuario_B = MockUser("User_B")
        usuario_A = MockUser("User_A", friends_list=[usuario_B])
        
        GestorEventos.registrarEvento(usuario_B.id, "EQUIPO_EDITADO", "Ha actualizado equipo Agua")
        
        notificaciones = GestorEventos.obtenerNotificaciones(usuario_A)
        self.assertTrue(any(n.tipo == "EQUIPO_EDITADO" for n in notificaciones))

    def test_cp_log_gen_03_captura(self):
        """ CP-LOG-GEN-03: Notificación Captura """
        usuario_B = MockUser("User_B")
        usuario_A = MockUser("User_A", friends_list=[usuario_B])
        
        GestorEventos.registrarEvento(usuario_B.id, "CAPTURA", "Ha capturado a Pikachu")
        
        notificaciones = GestorEventos.obtenerNotificaciones(usuario_A)
        self.assertTrue(any(n.descripcion == "Ha capturado a Pikachu" for n in notificaciones))

    def test_cp_log_gen_04_alcance_notificacion(self):
        """ CP-LOG-GEN-04: Alcance (No seguidores) """
        usuario_B = MockUser("User_B")
        usuario_C = MockUser("User_C", friends_list=[]) 
        
        GestorEventos.registrarEvento(usuario_B.id, "CAPTURA", "Mewtwo")
        
        notificaciones_C = GestorEventos.obtenerNotificaciones(usuario_C)
        self.assertEqual(len(notificaciones_C), 0, "Fallo: Usuario C vio notificaciones ajenas")

    def test_cp_log_gen_05_notificacion_propia(self):
        """ CP-LOG-GEN-05: Notificación Propia """
        usuario_B = MockUser("User_B", friends_list=[])
        
        GestorEventos.registrarEvento(usuario_B.id, "MI_LOGRO", "Subí de nivel")
        
        notificaciones = GestorEventos.obtenerNotificaciones(usuario_B)
        
        # Validamos comportamiento actual del código
        if len(notificaciones) > 0 and notificaciones[0].idUsuario == "User_B":
            print("\n[INFO] CP-LOG-GEN-05: Validado (Muestra notificaciones propias).")
        else:
            self.fail("Comportamiento inesperado en notificaciones propias.")

if __name__ == '__main__':
    unittest.main()