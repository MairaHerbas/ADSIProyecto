import os
import random # <--- IMPORTANTE: Necesario para la validación aleatoria
from flask import Flask, send_from_directory, jsonify, request

# --- VARIABLES DE CONFIGURACIÓN ---
PUERTO = 5000
MODO_DEBUG = True
CARPETA_RAIZ = os.getcwd()

# Inicialización de Flask
app = Flask(__name__)


IS_ADMIN = False  # <--- CAMBIAR AQUI PARA PROBAR

# --- BASE DE DATOS SIMULADA (En memoria) ---
DB_AMIGOS = {
    "friends": ["AshKetchum", "MistyWater", "BrockRock"],
    "pending": ["GaryOak", "TeamRocket_Jesse", "Giovanni", "NurseJoy"]
}


DB_ALL_USERS = [
    "AshKetchum", "MistyWater", "BrockRock", "GaryOak", "TeamRocket_Jesse", 
    "Giovanni", "NurseJoy", "ProfessorOak", "Cynthia_Champ", "RedMaster", 
    "BlueRival", "SilverRival", "GoldProtagonist", "CrystalClear", 
    "RubySapphire", "EmeraldRay", "DiamondPearl", "PlatinumGira", 
    "BlackWhite", "N_Harmonia", "Ghetsis", "LysandreLabs", "SerenaKalos"
]


DB_PENDING_ACCOUNTS = [
    "Newbie_123", "Trainer_X", "GlitchNo", "SpamBot_9000"
]

DB_NOTIFICATIONS = [
    {"user": "MistyWater", "type": "Intercambio", "date": "2025-05-09", "time": "14:30", "desc": "Te ha enviado un Staryu"},
    {"user": "BrockRock", "type": "Combate", "date": "2025-05-10", "time": "09:15", "desc": "Te ha desafiado a un duelo"},
    {"user": "AshKetchum", "type": "Mensaje", "date": "2025-05-08", "time": "18:45", "desc": "¡Vamos al gimnasio!"},
    {"user": "MistyWater", "type": "Intercambio", "date": "2025-05-02", "time": "11:20", "desc": "Ha aceptado tu Psyduck"},
    {"user": "GaryOak", "type": "Sistema", "date": "2025-05-10", "time": "10:05", "desc": "Ha aceptado tu solicitud de amistad"},
    {"user": "AshKetchum", "type": "Combate", "date": "2025-05-09", "time": "22:10", "desc": "Ha ganado el combate"},
]

user_profile = {
    "name": {"label": "Nombre Completo", "value": "Ash Ketchum", "editable": False},
    "email": {"label": "Correo Electrónico", "value": "ash@pokedex.com", "editable": True},
    "phone": {"label": "Teléfono", "value": "+34 600 999 999", "editable": True},
    "region": {"label": "Región", "value": "Kanto", "editable": False},
    "license": {"label": "Nº Licencia", "value": "ID-987654321", "editable": False},
    "motto": {"label": "Frase", "value": "¡Hazte con todos!", "editable": True}
}

# --- NUEVO: DB DE EQUIPOS (Con IDs para poder editarlos) ---
# He añadido IDs únicos para que el JS sepa cuál actualizar.
# --- DB DE EQUIPOS (Con miembros detallados) ---
DB_TEAMS = [
    {
        "id": "t1", "name": "Alpha Team", "pokemon_count": 3,
        "members": [
            {"name": "Charizard", "lvl": 55, "type": "Fuego"},
            {"name": "Pikachu", "lvl": 42, "type": "Eléctrico"},
            {"name": "Gengar", "lvl": 50, "type": "Fantasma"}
        ]
    },
    {
        "id": "t2", "name": "Beta Squad", "pokemon_count": 6,
        "members": [
            {"name": "Blastoise", "lvl": 60, "type": "Agua"},
            {"name": "Alakazam", "lvl": 58, "type": "Psíquico"},
            {"name": "Machamp", "lvl": 55, "type": "Lucha"},
            {"name": "Golem", "lvl": 52, "type": "Roca"},
            {"name": "Arcanine", "lvl": 54, "type": "Fuego"},
            {"name": "Exeggutor", "lvl": 53, "type": "Planta"}
        ]
    },
    {
        "id": "t3", "name": "Gym Defense", "pokemon_count": 1,
        "members": [{"name": "Snorlax", "lvl": 70, "type": "Normal"}]
    },
    # ... (Puedes añadir miembros falsos al resto o dejar la lista vacía si quieres ahorrar espacio)
    {"id": "t4", "name": "Shiny Hunt", "pokemon_count": 4, "members": [{"name": "Ponyta", "lvl": 10, "type": "Fuego"}]*4},
    {"id": "t5", "name": "PvP Master", "pokemon_count": 6, "members": [{"name": "Meta", "lvl": 100, "type": "?"}]*6},
    {"id": "t6", "name": "Reserves", "pokemon_count": 2, "members": [{"name": "Rattata", "lvl": 5, "type": "Normal"}]*2},
    {"id": "t7", "name": "Kanto Team", "pokemon_count": 6, "members": [{"name": "Kanto", "lvl": 50, "type": "?"}]*6},
    {"id": "t8", "name": "Johto Team", "pokemon_count": 3, "members": [{"name": "Johto", "lvl": 50, "type": "?"}]*3},
    {"id": "t9", "name": "Testing", "pokemon_count": 5, "members": [{"name": "Test", "lvl": 1, "type": "?"}]*5}
]


# --- MOCK DB: CAJA POKEMON GLOBAL ---
DB_BOX = [
    {"id": "p1", "name": "Bulbasaur", "lvl": 5, "type": "Planta"},
    {"id": "p2", "name": "Charmander", "lvl": 5, "type": "Fuego"},
    {"id": "p3", "name": "Squirtle", "lvl": 5, "type": "Agua"},
    {"id": "p4", "name": "Pikachu", "lvl": 12, "type": "Eléctrico"},
    {"id": "p5", "name": "Jigglypuff", "lvl": 8, "type": "Normal"},
    {"id": "p6", "name": "Meowth", "lvl": 10, "type": "Normal"},
    {"id": "p7", "name": "Psyduck", "lvl": 15, "type": "Agua"},
    {"id": "p8", "name": "Machop", "lvl": 14, "type": "Lucha"},
    {"id": "p9", "name": "Geodude", "lvl": 12, "type": "Roca"},
    {"id": "p10", "name": "Eevee", "lvl": 20, "type": "Normal"},
    {"id": "p11", "name": "Snorlax", "lvl": 30, "type": "Normal"},
    {"id": "p12", "name": "Mewtwo", "lvl": 70, "type": "Psíquico"},
    {"id": "p13", "name": "Magikarp", "lvl": 5, "type": "Agua"},
    {"id": "p14", "name": "Gyarados", "lvl": 25, "type": "Agua"},
    {"id": "p15", "name": "Dragonite", "lvl": 55, "type": "Dragón"},
]

# --- MOCK DB: ESPECIES (POKEDEX) ---
# Lista de todos los Pokémon que existen en el juego
DB_SPECIES = [
    {"id": 1, "name": "Bulbasaur", "type": "Planta"},
    {"id": 2, "name": "Ivysaur", "type": "Planta"},
    {"id": 3, "name": "Venusaur", "type": "Planta"},
    {"id": 4, "name": "Charmander", "type": "Fuego"},
    {"id": 5, "name": "Charmeleon", "type": "Fuego"},
    {"id": 6, "name": "Charizard", "type": "Fuego"},
    {"id": 7, "name": "Squirtle", "type": "Agua"},
    {"id": 8, "name": "Wartortle", "type": "Agua"},
    {"id": 9, "name": "Blastoise", "type": "Agua"},
    {"id": 25, "name": "Pikachu", "type": "Eléctrico"},
    {"id": 94, "name": "Gengar", "type": "Fantasma"},
    {"id": 133, "name": "Eevee", "type": "Normal"},
    {"id": 143, "name": "Snorlax", "type": "Normal"},
    {"id": 150, "name": "Mewtwo", "type": "Psíquico"},
    {"id": 151, "name": "Mew", "type": "Psíquico"},
]



# --- RUTAS PRINCIPALES ---
@app.route('/')
def servir_index():
    return send_from_directory(CARPETA_RAIZ, 'index.html')

@app.route('/<path:ruta_archivo>')
def servir_estaticos(ruta_archivo):
    return send_from_directory(CARPETA_RAIZ, ruta_archivo)

@app.route('/assets/<path:ruta_asset>')
def servir_assets(ruta_asset):
    return send_from_directory(os.path.join(CARPETA_RAIZ, 'assets'), ruta_asset)

# --- API AMIGOS ---
@app.route('/api/friends/data')
def get_friends_data():
    return jsonify(DB_AMIGOS)

@app.route('/api/friends/accept', methods=['POST'])
def accept_friend():
    data = request.json
    name = data.get('name')
    if name in DB_AMIGOS['pending']:
        DB_AMIGOS['pending'].remove(name)
        DB_AMIGOS['friends'].append(name)
        return jsonify({"status": "success", "msg": f"{name} aceptado"})
    return jsonify({"status": "error", "msg": "Usuario no encontrado"}), 404

@app.route('/api/friends/reject', methods=['POST'])
def reject_friend():
    data = request.json
    name = data.get('name')
    if name in DB_AMIGOS['pending']:
        DB_AMIGOS['pending'].remove(name)
        return jsonify({"status": "success", "msg": f"{name} rechazado"})
    return jsonify({"status": "error", "msg": "Usuario no encontrado"}), 404

@app.route('/api/friends/request', methods=['POST'])
def request_friend():
    data = request.json
    name = data.get('name')
    return jsonify({"status": "success", "msg": f"Solicitud enviada a {name}"})

@app.route('/api/friends/cancel', methods=['POST'])
def cancel_request():
    data = request.json
    name = data.get('name')
    return jsonify({"status": "success", "msg": f"Solicitud a {name} cancelada"})

@app.route('/api/friends/remove', methods=['POST'])
def remove_friend():
    data = request.json
    name = data.get('name')
    if name in DB_AMIGOS['friends']:
        DB_AMIGOS['friends'].remove(name)
        return jsonify({"status": "success", "msg": f"{name} eliminado"})
    return jsonify({"status": "error", "msg": "No encontrado"}), 404

@app.route('/api/users/available')
def get_available_users():
    excluded = set(DB_AMIGOS['friends'] + DB_AMIGOS['pending'])
    available = [user for user in DB_ALL_USERS if user not in excluded]
    available.sort()
    return jsonify(available)

# --- API NOTIFICACIONES ---
@app.route('/api/notifications')
def get_notifications():
    return jsonify(DB_NOTIFICATIONS)

# --- API DATOS USUARIO Y EQUIPOS ---
@app.route('/api/user-info')
def get_user_info():
    return jsonify({
        "username": "DEV_MASTER_01",
        "stats": "Rango: Admin | Ping: 12ms",
        "avatar_url": "https://api.dicebear.com/9.x/notionists/svg?seed=Felix&backgroundColor=ffdfbf",
        "teams": DB_TEAMS,
        "is_admin": IS_ADMIN  # <--- Enviamos el flag al frontend
    })

# --- API PERFIL (Edición) ---
@app.route('/api/profile-details', methods=['GET'])
def get_profile_details():
    fields = []
    for key, data in user_profile.items():
        fields.append({
            "id": key,
            "label": data["label"],
            "value": data["value"],
            "editable": data["editable"]
        })
    return jsonify({"title": "Datos de Entrenador", "fields": fields})

@app.route('/api/profile-update', methods=['POST'])
def update_profile():
    data = request.json
    field_id = data.get('id')
    new_value = data.get('value')
    if field_id in user_profile and user_profile[field_id]['editable']:
        user_profile[field_id]['value'] = new_value
        return jsonify({"success": True, "newValue": new_value})
    return jsonify({"success": False, "error": "Campo no editable o inexistente"}), 400

# --- NUEVO: API ACTUALIZAR EQUIPO (Simulación Random) ---
@app.route('/api/team-update', methods=['POST'])
def team_update():
    data = request.json
    team_id = data.get('id')
    new_name = data.get('name')
    new_members = data.get('members') # <--- NUEVO: Recibimos la lista de pokémon

    # Validación básica de nombre si se envía
    if new_name is not None and not new_name.strip():
        return jsonify({"success": False, "error": "El nombre no puede estar vacío"}), 400

    # SIMULACIÓN DE VALIDACIÓN (Random 50/50)
    # Nota: Esto hará que a veces falle al guardar a propósito, como pediste anteriormente.
    es_valido = random.choice([True, False])

    if es_valido:
        for team in DB_TEAMS:
            if team['id'] == team_id:
                # 1. Actualizar Nombre (si viene en la petición)
                if new_name:
                    team['name'] = new_name
                
                # 2. Actualizar Miembros (si viene en la petición) <--- CLAVE
                if new_members is not None:
                    team['members'] = new_members
                    team['pokemon_count'] = len(new_members) # Actualizar contador automáticamente

                return jsonify({
                    "success": True, 
                    "newName": team['name'],
                    "members": team['members'],
                    "pokemon_count": team['pokemon_count']
                })
        return jsonify({"success": False, "error": "Equipo no encontrado"}), 404
    else:
        return jsonify({"success": False, "error": "Error simulado (Random): Inténtalo de nuevo."}), 400



# --- OBTENER POKEMON DISPONIBLES PARA EDITAR ---
@app.route('/api/team-edit-available', methods=['POST'])
def team_edit_available():
    data = request.json
    team_id = data.get('id')
    
    # CASO 1: CREAR EQUIPO (ID es None/Null)
    # Si no hay ID, significa que es un equipo nuevo.
    # Devolvemos TODA la caja porque no hay miembros que excluir.
    if not team_id:
        return jsonify({
            "available": DB_BOX
        })

    # CASO 2: EDITAR EQUIPO EXISTENTE
    # Buscamos el equipo para excluir los pokemon que ya tiene
    current_team = next((t for t in DB_TEAMS if t['id'] == team_id), None)
    
    if not current_team:
        return jsonify({"error": "Equipo no encontrado"}), 404

    # Filtramos: Solo devolvemos los que NO estén ya en el equipo
    current_names = [m['name'] for m in current_team.get('members', [])]
    available = [p for p in DB_BOX if p['name'] not in current_names]
    
    return jsonify({
        "available": available
    })

@app.route('/api/team-delete', methods=['POST'])
def team_delete():
    data = request.json
    team_id = data.get('id')

    # Buscar el índice del equipo
    team_index = next((index for (index, d) in enumerate(DB_TEAMS) if d["id"] == team_id), None)

    if team_index is not None:
        deleted_team = DB_TEAMS.pop(team_index)
        return jsonify({"success": True, "msg": f"Equipo {deleted_team['name']} eliminado"})
    
    return jsonify({"success": False, "error": "Equipo no encontrado"}), 404


@app.route('/api/team-create', methods=['POST'])
def team_create():
    data = request.json
    new_name = data.get('name')
    new_members = data.get('members')

    # 1. Validaciones
    if not new_name or not new_name.strip():
        return jsonify({"success": False, "error": "El equipo necesita un nombre"}), 400
    
    if not new_members or len(new_members) == 0:
        return jsonify({"success": False, "error": "El equipo debe tener al menos 1 Pokémon"}), 400

    # 2. Generar ID (Simulado)
    # En producción usarías DB real. Aquí usamos 't' + timestamp o len
    new_id = f"t{len(DB_TEAMS) + 100}" 

    # 3. Crear Objeto
    new_team = {
        "id": new_id,
        "name": new_name,
        "pokemon_count": len(new_members),
        "members": new_members
    }

    # 4. Guardar (Simulación Random 50/50 de fallo como pediste antes, o éxito siempre?)
    # Para crear, mejor dejemos que tenga éxito siempre para no frustrar, 
    # o mantenemos el random si quieres testear errores.
    # Vamos a dejarlo con éxito siempre para diferenciarlo del editar.
    
    DB_TEAMS.append(new_team)
    
    return jsonify({
        "success": True, 
        "team": new_team
    })


# --- API POKEDEX ---
@app.route('/api/pokedex', methods=['GET'])
def get_pokedex():
    # Devolvemos la lista de especies y marcamos cuáles tiene el usuario
    # 1. Obtener nombres de los que ya tiene en la caja
    owned_names = {p['name'] for p in DB_BOX}
    
    pokedex_data = []
    for sp in DB_SPECIES:
        pokedex_data.append({
            "name": sp['name'],
            "type": sp['type'],
            "owned": sp['name'] in owned_names # True si ya lo tiene
        })
    
    return jsonify(pokedex_data)

@app.route('/api/pokedex/add', methods=['POST'])
def add_to_collection():
    data = request.json
    species_name = data.get('name')
    
    # Validar si existe la especie
    species = next((s for s in DB_SPECIES if s['name'] == species_name), None)
    if not species:
        return jsonify({"success": False, "error": "Especie desconocida"}), 404

    # Añadir a la CAJA del usuario (DB_BOX)
    new_instance = {
        "id": f"p{len(DB_BOX) + 1000}", # ID único
        "name": species['name'],
        "lvl": 1, # Empieza a nivel 1
        "type": species['type']
    }
    DB_BOX.append(new_instance)
    
    return jsonify({"success": True, "msg": f"{species_name} registrado en la Pokédex"})


# --- NUEVO: API ADMIN ---
@app.route('/api/admin/data')
def get_admin_data():
    if not IS_ADMIN:
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({
        "users": DB_ALL_USERS,
        "pending": DB_PENDING_ACCOUNTS
    })

@app.route('/api/admin/delete-user', methods=['POST'])
def admin_delete_user():
    data = request.json
    name = data.get('name')
    if name in DB_ALL_USERS:
        DB_ALL_USERS.remove(name)
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route('/api/admin/approve-user', methods=['POST'])
def admin_approve_user():
    data = request.json
    name = data.get('name')
    if name in DB_PENDING_ACCOUNTS:
        DB_PENDING_ACCOUNTS.remove(name)
        DB_ALL_USERS.append(name) # Mover a usuarios activos
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route('/api/admin/reject-user', methods=['POST'])
def admin_reject_user():
    data = request.json
    name = data.get('name')
    if name in DB_PENDING_ACCOUNTS:
        DB_PENDING_ACCOUNTS.remove(name)
        return jsonify({"success": True})
    return jsonify({"success": False}), 404


# --- EJECUCIÓN ---
if __name__ == '__main__':
    print(f"--> Servidor iniciado en: http://127.0.0.1:{PUERTO}")
    app.run(debug=MODO_DEBUG, port=PUERTO)