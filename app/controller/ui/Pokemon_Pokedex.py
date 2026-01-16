from flask import Blueprint, jsonify, render_template
from app.services.pokemon_loader import PokemonLoader
from app.controller.model.pokemon_db_controller import PokemonDBController

# Definimos el Blueprint para las rutas
pokedex_bp = Blueprint('pokedex_ui', __name__)

# --- RUTA 1: Para el Diagrama 1 (Sincronizar) ---
@pokedex_bp.route('/api/sincronizar', methods=['POST', 'GET'])
def sincronizar_bd():
    loader = PokemonLoader()
    exito = loader.importar_datos_api()
    if exito:
        return jsonify({"status": "success", "msg": "Pokemons descargados correctamente"})
    else:
        return jsonify({"status": "error", "msg": "Fallo en la descarga"}), 500

# --- RUTA 2: Para el Diagrama 2 (Obtener JSON para el Frontend) ---
@pokedex_bp.route('/api/pokemons/listar', methods=['GET'])
def listar_pokemons_json():
    # 1. Instanciar el controlador del modelo
    db_ctrl = PokemonDBController()
    # 2. Pedir los datos
    lista = db_ctrl.obtener_todos()
    # 3. Devolver JSON al frontend (logic.js)
    return jsonify(lista)