from functools import wraps
from flask import session, redirect, url_for, flash
from .models import User

def get_current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])

def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.home")) # Nota: "auth.home" referencia al Blueprint
        return view(*args, **kwargs)
    return wrapper

def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.home"))
        if session.get("role") != "admin":
            flash("No tienes permisos para acceder a Admin.", "danger")
            return redirect(url_for("auth.home"))
        return view(*args, **kwargs)
    return wrapper