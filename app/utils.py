from functools import wraps
from flask import session, jsonify
from app.controller.model.user_model import User


def get_current_user():
    if "user_id" not in session: return None
    # Usamos el método estático SQL que creamos antes
    return User.get_by_id(session["user_id"])


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            # CORRECCIÓN: Devolver JSON 401 en lugar de redirect
            return jsonify({"error": "Unauthorized", "redirect": "/"}), 401
        return view(*args, **kwargs)

    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        if session.get("role") != "admin":
            return jsonify({"error": "Forbidden", "msg": "Requiere permisos de administrador"}), 403

        return view(*args, **kwargs)

    return wrapper