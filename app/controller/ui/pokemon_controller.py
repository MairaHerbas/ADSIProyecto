from flask import Blueprint, request, jsonify, session
from datetime import datetime

from app.controller.model.pokemon_db_controller import PokemonDBController
from app.database.connection import db
# app/controller/ui/pokemon_controller.py
from app.controller.model.pokemon_model import Pokemon

from app.controller.model.team_model import Equipo, PokemonEquipo
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
#@login_required
def get_pokedex():
    # 1. Instanciamos el controlador de base de datos
    db_ctrl = PokemonDBController()

    # 2. Obtenemos los registros crudos (lista de diccionarios)
    all_pokemon = db_ctrl.obtener_todos()

    # 3. Formateamos la respuesta para el Frontend
    data = []

    # Simulación de capturados (Si tienes sistema de usuarios, aquí iría tu lógica de 'owned')
    # Por ahora lo dejamos vacío o con lógica simple
    owned_ids = set()
    if 'user_id' in session:
        # Aquí pondrías tu query para saber cuáles tiene el usuario
        pass

    for p in all_pokemon:
        # Convertimos los tipos "fire,flying" en array ["fire", "flying"]
        tipos_list = p['tipos'].split(',') if p['tipos'] else ['unknown']

        data.append({
            "id": p['id'],
            "name": p['nombre'],
            "sprite": p['imagen'],
            "types": tipos_list,
            "generation": p['generacion'],
            # Agrupamos las estadísticas para que queden ordenadas en el JSON
            "habilidades": p['habilidades'],
            "movimientos": p['movimientos'],
            "stats": {
                "hp": p['hp'],
                "atk": p['ataque'],
                "def": p['defensa'],
                "sp_atk": p['ataque_especial'],
                "sp_def": p['defensa_especial'],
                "spd": p['velocidad']
            },
            "owned": p['id'] in owned_ids
        })

    return jsonify(data)


@pokemon_bp.route('/api/pokedex/add', methods=['POST'])
@login_required
def add_to_pokedex():
    # Esta función simula capturar un pokemon desde la Dex.
    # Como tu diagrama solo contempla "Captura" al crear Equipos,
    # aquí devolvemos éxito simulado o podríamos crear una tabla 'Caja' en el futuro.
    return jsonify({"success": True, "msg": "Pokemon registrado (Simulación)"})

