from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..models import User
from ..extensions import db
from ..utils import login_required

# Creamos el "Blueprint"
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Credenciales incorrectas.", "danger")
            return render_template("welcome_login.html")

        if user.status == 'activo':
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role
            session.permanent = False
            flash(f"¡Bienvenido/a, {user.name}!", "success")
            return redirect(url_for("main.dashboard")) # Redirige al blueprint 'main'
        elif user.status == 'pendiente':
            flash('Tu cuenta todavía no ha sido aprobada por un administrador.', 'warning')
            return render_template("welcome_login.html")
        else:
            flash('Hay un problema con el estado de tu cuenta. Contacta al administrador.', 'danger')
            return render_template("welcome_login.html")

    return render_template("welcome_login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        username = (request.form.get("username") or "").strip().lower()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not name or not username or not email or not password or not confirm:
            flash("Rellena todos los campos.", "warning")
            return render_template("register.html")
        if password != confirm:
            flash("Las contraseñas no coinciden.", "warning")
            return render_template("register.html")
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "warning")
            return render_template("register.html")
        if User.query.filter_by(username=username).first():
            flash("Ese nombre de usuario ya está en uso. Elige otro.", "warning")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("Ya existe una cuenta con ese email.", "warning")
            return render_template("register.html")

        new_user = User(name=name, username=username, email=email, role="user")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("¡Cuenta creada! Está pendiente de aprobación por un administrador.", "info")
        return redirect(url_for("auth.home"))

    return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.home"))