from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from app.utils import get_current_user, login_required
from app.controller.model.user_model import User
from app.extensions import db
from app.services.services import ChangelogService

main_bp = Blueprint('main', __name__)


@main_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.home"))

    user = get_current_user()

    # --- LOGICA DEL APARTADO 3 (CHANGELOG) ---
    filtro = request.args.get('filtro_usuario')  # Capturamos el filtro de la URL

    # Usamos el servicio para obtener la lógica limpia
    eventos = ChangelogService.obtener_feed_amigos(user, filtro_usuario=filtro)
    # -----------------------------------------

    return render_template("dashboard.html",
                           name=session.get("user_name"),
                           role=session.get("role"),
                           eventos=eventos,  # Pasamos los eventos a la vista
                           filtro_actual=filtro)

    # return render_template("dashboard.html", name=session.get("user_name"), role=session.get("role"))


@main_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    user = get_current_user()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not name or not email:
            flash("El nombre y el email son obligatorios.", "warning")
            return render_template("profile_edit.html", user=user)

        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            flash("Ya existe otro usuario con ese email.", "warning")
            return render_template("profile_edit.html", user=user)

        if password:
            if password != confirm:
                flash("Las contraseñas no coinciden.", "warning")
                return render_template("profile_edit.html", user=user)
            if len(password) < 6:
                flash("La contraseña debe tener al menos 6 caracteres.", "warning")
                return render_template("profile_edit.html", user=user)
            user.set_password(password)

        user.name = name
        user.email = email
        db.session.commit()
        session["user_name"] = user.name

        flash("Datos actualizados correctamente.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("profile_edit.html", user=user)