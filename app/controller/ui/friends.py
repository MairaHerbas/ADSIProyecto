from flask import Blueprint, jsonify, request, session
from app.controller.model.user_model import User, FriendRequest
from app.utils import login_required

friends_bp = Blueprint('friends', __name__)


# --- 1. CARGAR DATOS ---
@friends_bp.route('/api/friends/data')
@login_required
def get_friends_data():
    me_id = session['user_id']
    user = User.get_by_id(me_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Amigos: Lista de objetos
    friends_list = user.friends
    friends_fmt = [{"name": f.username, "status": "online"} for f in friends_list]

    # Pendientes: Lista de objetos
    pending_list = FriendRequest.get_received_pending(me_id)
    pending_fmt = [{"name": p.sender_name} for p in pending_list]

    return jsonify({
        "friends": friends_fmt,
        "pending": pending_fmt
    })


# --- 2. ACEPTAR SOLICITUD ---
@friends_bp.route('/api/friends/accept', methods=['POST'])
@login_required
def accept_request():
    me_id = session['user_id']
    sender_name = request.json.get('name')

    sender = User.get_by_username(sender_name)
    if not sender:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

    # Buscamos la solicitud en la BD
    req = FriendRequest.get_existing(sender.id, me_id)

    # --- CORRECCIÓN CRÍTICA: USAR CORCHETES [] ---
    if req and req['status'] == 'pending':
        FriendRequest.accept(req['id'])
        return jsonify({"status": "success", "msg": f"Ahora eres amigo de {sender_name}"})

    return jsonify({"status": "error", "message": "No hay solicitud pendiente"}), 400


# --- 3. RECHAZAR SOLICITUD ---
@friends_bp.route('/api/friends/reject', methods=['POST'])
@login_required
def reject_request():
    me_id = session['user_id']
    sender_name = request.json.get('name')

    sender = User.get_by_username(sender_name)
    if not sender:
        return jsonify({"status": "error"}), 404

    req = FriendRequest.get_existing(sender.id, me_id)

    # --- CORRECCIÓN CRÍTICA: USAR CORCHETES [] ---
    if req:
        FriendRequest.reject(req['id'])
        return jsonify({"status": "success", "msg": "Solicitud rechazada"})

    return jsonify({"status": "error"}), 400


# --- 4. LISTAR CANDIDATOS ---
@friends_bp.route('/api/users/available')
@login_required
def get_available_users():
    me_id = session['user_id']
    candidates = User.get_friendship_candidates(me_id)
    return jsonify(candidates)


# --- 5. ENVIAR SOLICITUD ---
@friends_bp.route('/api/friends/request', methods=['POST'])
@login_required
def send_friend_request():
    me_id = session['user_id']
    target_username = request.json.get('name')

    target_user = User.get_by_username(target_username)
    if not target_user:
        return jsonify({"status": "error"}), 404

    existing = FriendRequest.get_existing(me_id, target_user.id)
    if existing:
        return jsonify({"status": "error", "message": "Ya pendiente"}), 400

    FriendRequest.create(me_id, target_user.id)
    return jsonify({"status": "success"})


# --- 6. CANCELAR SOLICITUD ---
@friends_bp.route('/api/friends/cancel', methods=['POST'])
@login_required
def cancel_sent_request():
    me_id = session['user_id']
    target_username = request.json.get('name')
    target_user = User.get_by_username(target_username)

    if target_user:
        req = FriendRequest.get_existing(me_id, target_user.id)
        if req:
            FriendRequest.reject(req['id'])  # Usar corchetes aquí también
            return jsonify({"status": "success"})

    return jsonify({"status": "error"}), 400


# --- 7. ELIMINAR AMIGO (ROMPE LA AMISTAD) ---
@friends_bp.route('/api/friends/remove', methods=['POST'])
@login_required
def remove_friend():
    me_id = session['user_id']
    target_username = request.json.get('name')

    target_user = User.get_by_username(target_username)

    if target_user:
        # Usamos el método estático que ya tenías en user_model.py
        # Esto borra la fila de la tabla 'friendship'
        FriendRequest.remove_friend(me_id, target_user.id)

        # Opcional: También podrías borrar la solicitud antigua 'accepted'
        # para limpiar basura, pero con borrar la friendship es suficiente
        # para que vuelva a salir en el buscador.

        return jsonify({"status": "success", "msg": f"Eliminado amigo: {target_username}"})

    return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404