from flask import Blueprint, request, jsonify, session
from app.controller.model.user_model import User

auth_bp = Blueprint('auth', __name__)


# --- API LOGIN ---
@auth_bp.route('/api/login', methods=['POST'])
def login():
    # 1. Recibir datos del usuario
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    # 2. Buscar usuario (Lógica original adaptada)
    user = User.get_by_email(email)

    if not user or not user.check_password(password):
        return jsonify({"success": False, "error": "Credenciales incorrectas"}), 401

    if user.status != 'activo':
        # Replica la lógica de 'pendiente' del auth.py original
        return jsonify({"success": False, "error": "Tu cuenta está pendiente de aprobación"}), 403

    # 3. Guardar en sesión
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['role'] = user.role

    return jsonify({"success": True, "msg": f"Bienvenido {user.name}", "redirect": "/"})


# --- API REGISTRO ---
@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name', '').strip()
    username = data.get('username', '').strip().lower()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm = data.get('confirm', '')  # Si el frontend envía confirmación

    # 1. Validaciones (Copiadas del auth.py original)
    if not name or not username or not email or not password:
        return jsonify({"success": False, "error": "Rellena todos los campos"}), 400

    if "@" not in email or "." not in email:
        return jsonify({"success": False, "error": "Email inválido"}), 400

    if confirm and password != confirm:
        return jsonify({"success": False, "error": "Las contraseñas no coinciden"}), 400

    if len(password) < 6:
        return jsonify({"success": False, "error": "La contraseña debe tener al menos 6 caracteres"}), 400

    # 2. Verificar duplicados en DB
    if User.get_by_username(username):
        return jsonify({"success": False, "error": "El nombre de usuario ya está en uso"}), 400

    if User.get_by_email(email):
        return jsonify({"success": False, "error": "El email ya está registrado"}), 400

    # 3. Crear usuario
    try:
        User.create(name, username, email, password)
        # Nota: El mensaje original decía "Pendiente de aprobación", pero aquí devolvemos éxito directo
        return jsonify({"success": True, "msg": "Cuenta creada correctamente. ¡Inicia sesión!"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error interno: {str(e)}"}), 500


# --- API LOGOUT ---
@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear() # Borra todos los datos de la sesión (id, role, etc.)
    return jsonify({"success": True, "msg": "Sesión cerrada"})