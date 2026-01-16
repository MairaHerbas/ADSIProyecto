from flask import Blueprint, jsonify, session, request
from app.controller.model.pokemon_db_model import PokemonDBController

pokemon_bp = Blueprint('pokemon_bp', __name__)


@pokemon_bp.route('/api/pokedex')
def get_pokedex():
    db = PokemonDBController()
    all_pokes = db.obtener_todos()

    # Usamos ID 1 si no hay usuario logueado (para pruebas)
    user_id = session.get('user_id', 1)

    # Obtenemos cuáles tiene este usuario
    owned_ids = db.obtener_capturados(user_id)

    data = []
    for p in all_pokes:
        tipos = p['tipos'].split(',') if p['tipos'] else []

        data.append({
            "id": p['id'],
            "name": p['nombre'],
            "sprite": p['imagen'],
            "types": tipos,
            "generation": p['generacion'],
            "habilidades": p['habilidades'],
            "movimientos": p['movimientos'],
            "stats": {
                "hp": p['hp'], "atk": p['ataque'], "def": p['defensa'],
                "sp_atk": p['ataque_especial'], "sp_def": p['defensa_especial'],
                "spd": p['velocidad']
            },
            # Marcamos TRUE si el ID está en la lista de capturados
            "owned": p['id'] in owned_ids
        })
    return jsonify(data)


@pokemon_bp.route('/api/pokedex/capture', methods=['POST'])
def capture_pokemon():
    data = request.json
    pokemon_id = data.get('pokemon_id')
    user_id = session.get('user_id', 1)

    if not pokemon_id:
        return jsonify({"success": False, "msg": "Falta ID"})

    db = PokemonDBController()
    nuevo_estado = db.toggle_captura(user_id, pokemon_id)

    return jsonify({"success": True, "captured": nuevo_estado})