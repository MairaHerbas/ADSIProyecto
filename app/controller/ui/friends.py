from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort
from app.controller.model.user_model import User, FriendRequest, friendship
from app.extensions import db
from app.utils import login_required, get_current_user

friends_bp = Blueprint('friends', __name__, url_prefix='/amistades')


@friends_bp.route("/")
@login_required
def gestionar_amistades():
    return render_template("amistades.html")


@friends_bp.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar_amigos():
    resultado_busqueda = None
    query = None

    if request.method == "POST":
        query = request.form.get("username_busqueda", "").strip().lower()
        if not query:
            flash("Por favor, introduce un nombre de usuario para buscar.", "warning")
            return redirect(url_for('friends.buscar_amigos'))

        resultado_busqueda = User.query.filter_by(username=query).first()
        if resultado_busqueda and resultado_busqueda.id == session['user_id']:
            flash("No puedes enviarte una solicitud a ti mismo.", "warning")
            resultado_busqueda = None

    return render_template("buscar_amigos.html", resultado=resultado_busqueda, query=query)


@friends_bp.post("/enviar/<int:user_id>")
@login_required
def enviar_solicitud(user_id):
    receiver = User.query.get_or_404(user_id)
    sender = get_current_user()

    if receiver.id == sender.id:
        flash("No puedes enviarte una solicitud a ti mismo.", "warning")
        return redirect(url_for('friends.buscar_amigos'))

    if sender.friends.filter(friendship.c.friend_id == receiver.id).count() > 0:
        flash(f"Ya eres amigo de {receiver.username}.", "info")
        return redirect(url_for('friends.buscar_amigos'))

    existing_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == sender.id) & (FriendRequest.receiver_id == receiver.id)) |
        ((FriendRequest.sender_id == receiver.id) & (FriendRequest.receiver_id == sender.id))
    ).filter(FriendRequest.status == 'pending').first()

    if existing_request:
        flash("Ya hay una solicitud de amistad pendiente con este usuario.", "warning")
        return redirect(url_for('friends.buscar_amigos'))

    new_request = FriendRequest(sender_id=sender.id, receiver_id=receiver.id)
    db.session.add(new_request)
    db.session.commit()

    flash(f"¡Solicitud de amistad enviada a {receiver.username}!", "success")
    return redirect(url_for('friends.buscar_amigos'))


@friends_bp.route("/solicitudes")
@login_required
def ver_solicitudes():
    current_user_id = session['user_id']
    solicitudes = FriendRequest.query.filter_by(
        receiver_id=current_user_id, status='pending'
    ).order_by(FriendRequest.created_at.desc()).all()
    return render_template("solicitudes_recibidas.html", solicitudes=solicitudes)


@friends_bp.post("/aceptar/<int:request_id>")
@login_required
def aceptar_solicitud(request_id):
    solicitud = FriendRequest.query.get_or_404(request_id)
    if solicitud.receiver_id != session['user_id']:
        abort(403)

    solicitud.status = 'accepted'
    usuario_actual = get_current_user()
    nuevo_amigo = solicitud.sender

    usuario_actual.friends.append(nuevo_amigo)
    nuevo_amigo.friends.append(usuario_actual)
    db.session.commit()

    flash(f"¡Ahora eres amigo de {nuevo_amigo.username}!", "success")
    return redirect(url_for('friends.ver_solicitudes'))


@friends_bp.post("/rechazar/<int:request_id>")
@login_required
def rechazar_solicitud(request_id):
    solicitud = FriendRequest.query.get_or_404(request_id)
    if solicitud.receiver_id != session['user_id']:
        abort(403)

    db.session.delete(solicitud)
    db.session.commit()
    flash(f"Solicitud de {solicitud.sender.username} rechazada.", "info")
    return redirect(url_for('friends.ver_solicitudes'))


@friends_bp.route("/lista")
@login_required
def ver_amigos():
    current_user = get_current_user()
    lista_amigos = current_user.friends.order_by(User.username).all()
    return render_template("ver_amigos.html", lista_amigos=lista_amigos)


@friends_bp.post("/eliminar/<int:friend_id>")
@login_required
def eliminar_amigo(friend_id):
    current_user = get_current_user()
    friend_to_remove = User.query.get_or_404(friend_id)

    current_user.friends.remove(friend_to_remove)
    friend_to_remove.friends.remove(current_user)
    db.session.commit()

    flash(f"Has eliminado a {friend_to_remove.username} de tu lista de amigos.", "info")
    return redirect(url_for('friends.ver_amigos'))