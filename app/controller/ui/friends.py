from flask import Blueprint, request, jsonify, session
from app.controller.model.user_model import User, FriendRequest
from app.utils import login_required, get_current_user

friends_bp = Blueprint('friends', __name__)


@friends_bp.route('/api/friends/data')
@login_required
def get_friends_data():
    me = get_current_user()
    if not me: return jsonify({"error": "No user"}), 401

    # Obtener amigos y solicitudes usando los métodos SQL
    amigos_list = [u.username for u in me.friends]

    pending_reqs = FriendRequest.get_received_pending(me.id)
    pendientes_list = [req.sender_name for req in pending_reqs]

    return jsonify({
        "friends": amigos_list,
        "pending": pendientes_list
    })


@friends_bp.route('/api/friends/request', methods=['POST'])
@login_required
def request_friend():
    data = request.json
    target_username = data.get('name')
    me = get_current_user()

    target = User.get_by_username(target_username)
    if not target:
        return jsonify({"status": "error", "msg": "Usuario no encontrado"}), 404

    if target.id == me.id:
        return jsonify({"status": "error", "msg": "No puedes enviarte solicitud a ti mismo"})

    # Verificar si ya son amigos
    if any(f.id == target.id for f in me.friends):
        return jsonify({"status": "error", "msg": "Ya sois amigos"})

    # Verificar si ya hay solicitud pendiente
    if FriendRequest.get_existing(me.id, target.id):
        return jsonify({"status": "error", "msg": "Ya hay una solicitud pendiente"})

    FriendRequest.create(me.id, target.id)
    return jsonify({"status": "success", "msg": f"Solicitud enviada a {target_username}"})


@friends_bp.route('/api/friends/accept', methods=['POST'])
@login_required
def accept_friend():
    data = request.json
    sender_name = data.get('name')
    me = get_current_user()

    # Buscar la solicitud por nombre del remitente
    pending = FriendRequest.get_received_pending(me.id)
    req_to_accept = next((r for r in pending if r.sender_name == sender_name), None)

    if req_to_accept:
        FriendRequest.accept(req_to_accept.id)
        return jsonify({"status": "success", "msg": f"{sender_name} aceptado"})

    return jsonify({"status": "error", "msg": "Solicitud no encontrada"}), 404


@friends_bp.route('/api/friends/reject', methods=['POST'])
@login_required
def reject_friend():
    data = request.json
    sender_name = data.get('name')
    me = get_current_user()

    pending = FriendRequest.get_received_pending(me.id)
    req_to_reject = next((r for r in pending if r.sender_name == sender_name), None)

    if req_to_reject:
        FriendRequest.reject(req_to_reject.id)
        return jsonify({"status": "success", "msg": "Solicitud rechazada"})

    return jsonify({"status": "error", "msg": "Solicitud no encontrada"}), 404


@friends_bp.route('/api/friends/remove', methods=['POST'])
@login_required
def remove_friend():
    data = request.json
    friend_name = data.get('name')
    me = get_current_user()

    friend = User.get_by_username(friend_name)
    if friend:
        FriendRequest.remove_friend(me.id, friend.id)
        return jsonify({"status": "success", "msg": "Amigo eliminado"})

    return jsonify({"status": "error", "msg": "Usuario no encontrado"}), 404