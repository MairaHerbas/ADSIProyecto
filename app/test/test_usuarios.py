import pytest
import json
from app import create_app
from app.controller.model.user_model import User
from app.database.connection import db


# --- CONFIGURACIÓN DE PRUEBAS (FIXTURE) ---

@pytest.fixture
def client():
    """
    Configura un cliente de pruebas (navegador simulado).
    Se ejecuta ANTES de cada test para limpiar la base de datos.
    """
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Desactivar CSRF para tests de API

    with app.test_client() as client:
        with app.app_context():
            # 1. LIMPIEZA: Borrar datos de pruebas anteriores
            # Usamos db.insert porque tu wrapper usa esto para ejecutar SQL
            tables = ["pokemon_equipo", "equipo", "friend_request", "friendship", "user", "Changelog_Event"]
            try:
                for t in tables:
                    db.insert(f"DROP TABLE IF EXISTS {t}")
            except Exception as e:
                print(f"Error limpiando DB: {e}")

            # 2. INICIALIZACIÓN: Crear tablas limpias
            from app import init_tables
            init_tables()

        yield client


# --- FUNCIONES DE AYUDA (HELPERS) ---

def login(client, email, password):
    return client.post('/api/login', json={'email': email, 'password': password})


def register(client, name, username, email, password):
    return client.post('/api/register', json={
        'name': name, 'username': username, 'email': email, 'password': password
    })


# ==========================================
#   CASOS DE PRUEBA (Según PDF ADSI)
# ==========================================

# --- 3.1.1. REGISTRO ---

def test_cp_reg_01_registro_exitoso(client):
    """CP-REG-01: Registro Positivo. Verifica que la cuenta nace 'pendiente'."""
    res = register(client, "Test User", "testuser", "test@mail.com", "123456")
    data = res.get_json()

    assert res.status_code == 200
    assert data['success'] is True

    # --- CORRECCIÓN AQUÍ ---
    # Cambiamos "Espera a ser aprobado" por "Espera aprobación"
    assert "Espera aprobación" in data['msg']

    # Verificar en BD que el estado es pendiente
    user = User.get_by_email("test@mail.com")
    assert user is not None
    assert user.status == 'pendiente'

def test_cp_reg_05_registro_duplicado(client):
    """CP-REG-05: Registro Negativo (Duplicado)."""
    register(client, "User 1", "u1", "dup@mail.com", "123")

    # Intento de registro con mismo email
    res = register(client, "User 2", "u2", "dup@mail.com", "123")
    data = res.get_json()

    assert res.status_code == 400
    assert data['success'] is False
    assert "ya está registrado" in data['error']


# --- 3.1.1. INICIO DE SESIÓN ---

def test_cp_log_02_login_pendiente(client):
    """CP-LOG-02: Login Negativo (Cuenta Pendiente)."""
    # Registrar (nace pendiente)
    register(client, "Pending", "pending", "pend@mail.com", "123")

    # Intentar entrar
    res = login(client, "pend@mail.com", "123")
    data = res.get_json()

    assert res.status_code == 403
    assert data['success'] is False
    assert "pendiente de aprobación" in data['error']


def test_cp_log_01_login_exitoso(client):
    """CP-LOG-01: Login Positivo (Cuenta Aprobada)."""
    register(client, "Active", "active", "active@mail.com", "123")

    # Aprobar manualmente (Simulando Admin)
    user = User.get_by_email("active@mail.com")
    User.update_status(user.id, 'aprobado')

    # Login
    res = login(client, "active@mail.com", "123")
    data = res.get_json()

    assert res.status_code == 200
    assert data['success'] is True


def test_cp_log_03_pass_incorrecta(client):
    """CP-LOG-03: Login Negativo (Contraseña Mal)."""
    register(client, "User", "user", "user@mail.com", "123")
    # Aprobamos para asegurar que el fallo sea por pass y no por status
    u = User.get_by_email("user@mail.com")
    User.update_status(u.id, 'aprobado')

    res = login(client, "user@mail.com", "badpass")
    assert res.status_code == 401


# --- 3.1.3. ADMINISTRACIÓN ---

def test_cp_adm_01_aprobar_cuenta(client):
    """CP-ADM-01: Admin aprueba cuenta pendiente."""
    # 1. Crear Admin (usando create directo para forzar rol)
    User.create("Admin", "admin", "admin@demo.com", "123", role="admin", status="aprobado")

    # 2. Crear Usuario Pendiente
    register(client, "User P", "upend", "upend@mail.com", "123")
    target = User.get_by_email("upend@mail.com")

    # 3. Login como Admin
    login(client, "admin@demo.com", "123")

    # 4. Aprobar usuario (Llamada a API Admin)
    res = client.post(f'/api/admin/user/{target.id}/status', json={'status': 'aprobado'})
    assert res.status_code == 200

    # 5. Verificar que cambió en BD
    updated = User.get_by_id(target.id)
    assert updated.status == 'aprobado'


# --- 3.1.4. GESTIÓN DE AMIGOS ---

def test_cp_ami_01_flujo_amistad(client):
    """CP-AMI-01 y CP-AMI-05: Enviar y Aceptar solicitud."""
    # Setup: 2 usuarios aprobados
    User.create("Ash", "ash", "ash@pk.com", "123", role="user", status="aprobado")
    User.create("Misty", "misty", "misty@pk.com", "123", role="user", status="aprobado")

    # 1. Ash envía solicitud a Misty
    login(client, "ash@pk.com", "123")
    res = client.post('/api/friends/request', json={'name': 'misty'})
    assert res.status_code == 200
    assert res.get_json()['status'] == 'success'

    # 2. Misty Acepta
    login(client, "misty@pk.com", "123")
    # Nota: la API espera el nombre del que envió (Ash)
    res = client.post('/api/friends/accept', json={'name': 'ash'})
    data = res.get_json()

    assert res.status_code == 200
    assert "Ahora eres amigo" in data['msg']

    # 3. Verificar lista de amigos
    res_list = client.get('/api/friends/data')
    friends_list = res_list.get_json()['friends']  # Lista de objetos
    names = [f['name'] for f in friends_list]
    assert "ash" in names