from flask import Blueprint, jsonify, session
from app.controller.model.team_model import Equipo
from app.utils import login_required
# ✅ ESTA ES LA LÍNEA QUE TE FALTA:
from app.controller.model.user_model import User

main_bp = Blueprint('main', __name__)


@main_bp.route('/api/user-info')
def get_user_info():
    # 1. Verificar sesión
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']

    # 2. Obtener DATOS REALES (Ahora funcionará porque User ya está importado)
    user = User.get_by_id(user_id)

    if not user:
        session.clear()
        return jsonify({"error": "Usuario no existe"}), 404

    # 3. Obtener equipos
    equipos_raw = Equipo.get_by_user(user_id)
    equipos_json = []

    for eq in equipos_raw:
        miembros = Equipo.get_members(eq['id'])
        miembros_fmt = [{
            "pokemon_id": m['pokemon_id'],
            "name": m['nombre'],
            "type": m['tipos'].split(',')[0] if m['tipos'] else "Normal",
            "lvl": 50,
            "sprite": m['imagen_url']
        } for m in miembros]

        equipos_json.append({
            "id": eq['id'],
            "name": eq['nombre_equipo'],
            "pokemon_count": len(miembros),
            "members": miembros_fmt
        })

    # 4. Retorno FINAL
    return jsonify({
        "username": user.username,
        "name": getattr(user, 'name', user.username),
        "email": user.email,
        "role": user.role,
        "is_admin": (user.role == 'admin'),  # Esto es lo que busca el JS
        "status": getattr(user, 'status', 'aprobado'),
        "avatar_url": f"https://api.dicebear.com/9.x/notionists/svg?seed={user.username}",
        "teams": equipos_json
    })