# app/controller/ui/team_controller.py
from flask import Blueprint, request, jsonify, session
from app.utils import login_required
from app.controller.model.team_model import Equipo, PokemonEquipo
from app.controller.model.pokemon_model import Pokemon
from app.services.services import ChangelogService

team_bp = Blueprint('team', __name__)


# --- CARGAR CAJA ---
@team_bp.route('/api/team-edit-available', methods=['POST'])
@login_required
def team_edit_available():
    # ... (Mismo código que ya tienes para listar pokemons) ...
    pokemons = Pokemon.get_all()
    available = [{"pokemon_id": dict(p)['id'], "name": dict(p)['nombre'], "sprite": dict(p)['imagen_url'],
                  "type": dict(p)['tipos'].split(',')[0] if dict(p)['tipos'] else "Normal", "lvl": 1} for p in pokemons]
    return jsonify({"available": available})


# --- CUMPLE PUNTO 4: Crear Equipo Vacío Inicial ---
@team_bp.route('/api/team/init', methods=['POST'])
@login_required
def team_init():
    user_id = session['user_id']
    # 1. Insertamos equipo vacío inmediatamente
    # (Diagrama Secuencia: Crear -> Insertar Equipo Vacío)
    new_id = Equipo.create(user_id, "Nuevo Equipo")

    # 2. Devolvemos el ID para que el frontend entre en modo edición
    return jsonify({"success": True, "id": new_id, "name": "Nuevo Equipo"})


# --- CUMPLE PUNTO 3: Actualizaciones Inmediatas (Nombre) ---
@team_bp.route('/api/team/set-name', methods=['POST'])
@login_required
def team_set_name():
    data = request.json
    Equipo.update(data['id'], data['name'])
    return jsonify({"success": True})


# --- CUMPLE PUNTO 3 y 5: Añadir Miembro (Inmediato) ---
@team_bp.route('/api/team/add-member', methods=['POST'])
@login_required
def team_add_member():
    data = request.json
    team_id = data['team_id']
    poke_id = data['pokemon_id']

    # Calculamos el orden (simulado, o podrías enviarlo desde front)
    current_members = Equipo.get_members(team_id)
    orden = len(current_members) + 1

    if orden > 6:
        return jsonify({"success": False, "error": "Equipo lleno"})

    PokemonEquipo.create(team_id, poke_id, orden)
    return jsonify({"success": True})


# --- CUMPLE PUNTO 3: Quitar Miembro (Inmediato) ---
@team_bp.route('/api/team/remove-member', methods=['POST'])
@login_required
def team_remove_member():
    data = request.json
    # Ojo: Aquí tu modelo necesita un delete específico por pokemon y equipo
    # Para simplificar, asumimos que borras por ID de equipo y Pokemon,
    # o idealmente por un ID único de la tabla intermedia si lo tuvieras.
    # Usaremos una nueva función en el modelo:
    PokemonEquipo.delete_one(data['team_id'], data['pokemon_id'])
    return jsonify({"success": True})


# --- ELIMINAR EQUIPO COMPLETO ---
@team_bp.route('/api/team-delete', methods=['POST'])
@login_required
def team_delete():
    data = request.json
    Equipo.delete(data['id'])
    return jsonify({"success": True})