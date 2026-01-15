from flask import Blueprint, jsonify, session
from app.controller.model.pokemon_model import Equipo
from app.utils import login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/api/user-info')
@login_required
def get_user_info():
    user_id = session['user_id']
    username = session.get('user_name', 'Entrenador')  # Guardado en login
    role = session.get('role', 'user')

    # Obtener equipos con SQL
    equipos_raw = Equipo.get_by_user(user_id)

    # Formatear para frontend
    equipos_json = []
    for eq in equipos_raw:
        miembros = Equipo.get_members(eq['id'])
        # Adaptar formato de miembros
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

    return jsonify({
        "username": username,
        "stats": f"Rango: {role}",
        "avatar_url": f"https://api.dicebear.com/9.x/notionists/svg?seed={username}",
        "teams": equipos_json,
        "is_admin": (role == 'admin')
    })