# app/controller/ui/team_controller.py
from flask import Blueprint, request, jsonify, session
from app.utils import login_required
from app.controller.model.team_model import Equipo, PokemonEquipo
from app.controller.model.pokemon_model import Pokemon
# Importamos para filtrar capturados
from app.controller.model.pokemon_db_controller import PokemonDBController

team_bp = Blueprint('team', __name__)


# --- CARGAR CAJA ---
@team_bp.route('/api/team-edit-available', methods=['POST'])
@login_required
def team_edit_available():
    user_id = session['user_id']

    # 1. Todos los pokemons base
    pokemons = Pokemon.get_all()

    # 2. Capturados por el usuario
    db_ctrl = PokemonDBController()
    capturados_ids = db_ctrl.obtener_capturados(user_id)

    # 3. Filtrar y construir JSON
    available = []
    for p in pokemons:
        p_dict = dict(p)
        # Solo añadimos si está capturado
        if p_dict['id'] in capturados_ids:
            # CORRECCIÓN AQUÍ: Usamos p_dict['imagen'] en lugar de ['imagen_url']
            available.append({
                "pokemon_id": p_dict['id'],
                "name": p_dict['nombre'],
                "sprite": p_dict['imagen'],
                "type": p_dict['tipos'].split(',')[0] if p_dict['tipos'] else "Normal",
                "lvl": 1
            })

    return jsonify({"available": available})


# --- CREAR EQUIPO VACÍO ---
@team_bp.route('/api/team/init', methods=['POST'])
@login_required
def team_init():
    user_id = session['user_id']
    new_id = Equipo.create(user_id, "Nuevo Equipo")
    return jsonify({"success": True, "id": new_id, "name": "Nuevo Equipo"})


# --- ACTUALIZAR NOMBRE ---
@team_bp.route('/api/team/set-name', methods=['POST'])
@login_required
def team_set_name():
    data = request.json
    Equipo.update(data['id'], data['name'])
    return jsonify({"success": True})


# --- AÑADIR MIEMBRO ---
@team_bp.route('/api/team/add-member', methods=['POST'])
@login_required
def team_add_member():
    data = request.json
    team_id = data['team_id']
    poke_id = data['pokemon_id']

    current_members = Equipo.get_members(team_id)
    orden = len(current_members) + 1

    if orden > 6:
        return jsonify({"success": False, "error": "Equipo lleno"})

    PokemonEquipo.create(team_id, poke_id, orden)
    return jsonify({"success": True})


# --- QUITAR MIEMBRO ---
@team_bp.route('/api/team/remove-member', methods=['POST'])
@login_required
def team_remove_member():
    data = request.json
    PokemonEquipo.delete_one(data['team_id'], data['pokemon_id'])
    return jsonify({"success": True})


# --- ELIMINAR EQUIPO ---
@team_bp.route('/api/team-delete', methods=['POST'])
@login_required
def team_delete():
    data = request.json
    Equipo.delete(data['id'])
    return jsonify({"success": True})