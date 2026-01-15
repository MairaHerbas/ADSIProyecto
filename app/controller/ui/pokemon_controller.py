from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app.database.connection import db
from app.controller.model.pokemon_model import Equipo, Pokemon, PokemonEquipo
from app.controller.model.user_model import Event
from app.utils import login_required

pokemon_bp = Blueprint('pokemon', __name__)


# --- HELPER: Convertir Objeto DB a JSON ---
def serializar_equipo(equipo):
    miembros = []
    # Obtenemos miembros usando el método estático que creamos en el modelo
    # o si usas la relación de SQLAlchemy adaptada (que aquí no aplica por ser SQL puro),
    # usamos la consulta directa:
    miembros_raw = Equipo.get_members(equipo.id)

    for m in miembros_raw:
        miembros.append({
            "pokemon_id": m['pokemon_id'],
            "name": m['nombre'],
            "type": m['tipos'].split(',')[0] if m['tipos'] else "Normal",
            "lvl": 50,
            "apodo": m['apodo'],
            "sprite": m['imagen_url']
        })
    return {
        "id": equipo.id,
        "name": equipo.nombre_equipo,
        "pokemon_count": len(miembros),
        "members": miembros
    }


# --- API: POKEDEX (LA QUE FALTABA) ---
@pokemon_bp.route('/api/pokedex')
@login_required
def get_pokedex():
    # 1. Obtener todos los 386 pokemon de tu DB
    all_pokemon = Pokemon.get_all()

    # 2. Consultar cuáles tiene el usuario (para marcar 'owned')
    # Buscamos IDs de pokemon que estén en CUALQUIERA de tus equipos
    user_id = session['user_id']
    sql_owned = """
        SELECT DISTINCT pokemon_id 
        FROM pokemon_equipo 
        JOIN equipo ON pokemon_equipo.equipo_id = equipo.id 
        WHERE equipo.user_id = ?
    """
    owned_rows = db.select(sql_owned, (user_id,))
    owned_ids = {row['pokemon_id'] for row in owned_rows}

    # 3. Formatear JSON para el frontend
    data = []
    for row in all_pokemon:
        p = dict(row)  # Convertir Row a diccionario
        data.append({
            "id": p['id'],
            "name": p['nombre'],
            # Tomamos el primer tipo si hay varios
            "type": p['tipos'].split(',')[0] if p['tipos'] else "Normal",
            "owned": p['id'] in owned_ids,  # True si lo tienes en un equipo
            "sprite": p['imagen_url']
        })

    return jsonify(data)


@pokemon_bp.route('/api/pokedex/add', methods=['POST'])
@login_required
def add_to_pokedex():
    # Esta función simula capturar un pokemon desde la Dex.
    # Como tu diagrama solo contempla "Captura" al crear Equipos,
    # aquí devolvemos éxito simulado o podríamos crear una tabla 'Caja' en el futuro.
    return jsonify({"success": True, "msg": "Pokemon registrado (Simulación)"})


# --- API: DISPONIBLES (CAJA PARA EDITAR EQUIPO) ---
@pokemon_bp.route('/api/team-edit-available', methods=['POST'])
@login_required
def team_edit_available():
    pokemons = Pokemon.get_all()
    # Formato simplificado para la caja