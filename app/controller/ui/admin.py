from flask import Blueprint, jsonify, request, session
from app.controller.model.user_model import User
from app.utils import admin_required

# Quitamos el url_prefix para simplificar las rutas de la API
admin_bp = Blueprint('admin', __name__)


# --- 1. RUTA DE DATOS (ESTA ES LA QUE CARGA TU TABLA) ---
@admin_bp.route('/api/admin/dashboard-data')
@admin_required
def get_dashboard_data():
    """
    Devuelve los usuarios en formato JSON para que el JavaScript
    pueda pintar la lista de pendientes y el buscador.
    """
    search_query = request.args.get('q', '')

    # A. Buscar PENDIENTES (Para la caja amarilla)
    # IMPORTANTE: Asegúrate de haber añadido el método filter_users a tu modelo User
    try:
        pendientes_raw = User.filter_users(status='pendiente')
    except AttributeError:
        # Si da error, es que no actualizaste user_model.py en el paso anterior.
        # Devuelve lista vacía para no romper la app.
        print("ERROR: Falta filter_users en User Model")
        pendientes_raw = []

    # B. Buscar RESTO DE USUARIOS (Para la lista azul)
    try:
        usuarios_raw = User.filter_users(search=search_query)
    except:
        usuarios_raw = []

    # Filtramos para que los pendientes no salgan duplicados abajo
    usuarios_limpios = [u for u in usuarios_raw if u.status != 'pendiente']

    # Función para convertir Objeto Python -> JSON
    def format_user(u):
        return {
            "id": u.id,
            "name": u.name,
            "username": u.username,
            "email": u.email,
            "status": u.status,  # 'pendiente', 'aprobado', 'bloqueado'
            "date": str(u.created_at).split()[0] if u.created_at else ""
        }

    return jsonify({
        "pending": [format_user(u) for u in pendientes_raw],
        "directory": [format_user(u) for u in usuarios_limpios]
    })


# --- 2. RUTA DE ACCIÓN (APROBAR / BLOQUEAR) ---
@admin_bp.route('/api/admin/user/<int:user_id>/status', methods=['POST'])
@admin_required
def change_status(user_id):
    data = request.json
    new_status = data.get('status')  # 'aprobado' o 'bloqueado'

    # Seguridad básica
    if new_status not in ['aprobado', 'bloqueado', 'pendiente']:
        return jsonify({"error": "Estado no válido"}), 400

    if user_id == session.get('user_id'):
        return jsonify({"error": "No puedes modificar tu propio usuario"}), 403

    # Ejecutar cambio en BD
    # Nota: Asegúrate de tener update_status en tu modelo User
    User.update_status(user_id, new_status)

    return jsonify({"success": True})


# --- 3. RUTA DE BORRADO (NUEVA) ---
@admin_bp.route('/api/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user_route(user_id):
    # 1. Seguridad: No puedes borrarte a ti mismo
    if user_id == session.get('user_id'):
        return jsonify({"error": "No puedes borrar tu propia cuenta."}), 403

    # 2. Seguridad: Obtener usuario para ver si es el Super Admin
    user_to_delete = User.get_by_id(user_id)
    if not user_to_delete:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if user_to_delete.role == 'admin':
        return jsonify({"error": "No puedes eliminar a un administrador."}), 403

    # 3. Proceder al borrado
    User.delete(user_id)

    return jsonify({"success": True})


# --- 4. RUTA DE CAMBIO DE ROL (ASCENDER/DEGRADAR) ---
@admin_bp.route('/api/admin/user/<int:user_id>/role', methods=['POST'])
@admin_required
def change_role_route(user_id):
    data = request.json
    new_role = data.get('role')  # 'admin' o 'user'

    if new_role not in ['admin', 'user']:
        return jsonify({"error": "Rol inválido"}), 400

    # 1. Obtener usuario objetivo
    target_user = User.get_by_id(user_id)
    if not target_user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # 2. SEGURIDAD: Proteger al Super Admin
    # Si intentan degradar al usuario 'admin' o al correo principal
    if target_user.username == 'admin' or target_user.email == 'admin@demo.com':
        return jsonify({"error": "El Administrador Principal no puede ser degradado."}), 403

    # 3. SEGURIDAD: No puedes cambiar tu propio rol (te bloquearías a ti mismo)
    if user_id == session.get('user_id'):
        return jsonify({"error": "No puedes cambiar tu propio rol."}), 403

    # 4. Aplicar cambio
    User.update_role(user_id, new_role)

    action = "ascendido a Admin" if new_role == 'admin' else "degradado a Usuario"
    return jsonify({"success": True, "msg": f"Usuario {action}."})