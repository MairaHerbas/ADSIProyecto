from flask import Blueprint, request, jsonify, session
from app.controller.model.user_model import User

auth_bp = Blueprint('auth', __name__)


# --- API LOGIN ---
@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    # Buscar usuario por email
    user = User.get_by_email(email)

    if user and user.check_password(password):

        # --- 🛑 NUEVA REGLA: VERIFICAR ESTADO ---
        # Si el usuario tiene atributo status y no es 'aprobado'
        current_status = getattr(user, 'status', 'aprobado')  # Por defecto aprobado si no existe campo

        if current_status == 'pendiente':
            return jsonify({
                "success": False,
                "error": "Tu cuenta está pendiente de aprobación por un Administrador."
            }), 403  # Forbidden

        if current_status == 'bloqueado':
            return jsonify({"success": False, "error": "Esta cuenta ha sido bloqueada."}), 403

        # --- LOGIN EXITOSO ---
        session["user_id"] = user.id
        session["user_name"] = user.username
        session["role"] = user.role

        return jsonify({"success": True, "msg": "Login correcto", "role": user.role})

    return jsonify({"success": False, "error": "Credenciales inválidas"}), 401


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.json

    # 1. Validar campos obligatorios
    if not data or not data.get("username") or not data.get("email"):
        return jsonify({"success": False, "error": "Faltan datos"}), 400

    # 2. 🛑 COMPROBAR DUPLICADOS (EMAIL Y USUARIO)
    if User.get_by_email(data.get("email")):
        return jsonify({"success": False, "error": "El email ya está registrado."}), 400

    if User.get_by_username(data.get("username")):  # <--- NUEVA COMPROBACIÓN
        return jsonify({"success": False, "error": "El nombre de usuario ya está en uso."}), 400

    # 3. Crear usuario
    try:
        new_user = User.create(
            name=data.get("name"),
            username=data.get("username"),
            email=data.get("email"),
            password=data.get("password"),
            role="user",
            status="pendiente"
        )

        if new_user:
            return jsonify({"success": True, "msg": "Cuenta creada. Espera aprobación."})
        else:
            return jsonify({"success": False, "error": "Error en base de datos"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": f"Error: {str(e)}"}), 500
# --- API LOGOUT ---
@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear() # Borra todos los datos de la sesión (id, role, etc.)
    return jsonify({"success": True, "msg": "Sesión cerrada"})


@auth_bp.route("/api/profile-details")
def profile_details():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.get_by_id(session["user_id"])
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    real_name = getattr(user, 'name', '')
    username = getattr(user, 'username', '')
    email = getattr(user, 'email', '')

    return jsonify({
        "title": "DATOS DE LA CUENTA",
        "fields": [
            {
                "id": "name",
                "label": "NOMBRE COMPLETO",
                "value": real_name,
                "editable": True  # Este es el único que dejaremos cambiar
            },
            {
                "id": "username",
                "label": "NOMBRE DE USUARIO",
                "value": username,
                "editable": False # 🔒 AHORA BLOQUEADO
            },
            {
                "id": "email",
                "label": "CORREO ELECTRÓNICO",
                "value": email,
                "editable": False # 🔒 BLOQUEADO
            },
            {
                "id": "password",
                "label": "CONTRASEÑA",
                "value": "********",
                "editable": True
            }
        ]
    })