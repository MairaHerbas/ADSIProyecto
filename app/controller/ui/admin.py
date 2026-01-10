from flask import Blueprint, render_template, flash, redirect, url_for, session
from app.controller.model.user_model import User
from app.extensions import db
from app.utils import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/")
@admin_required
def admin_panel():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin.html", users=users, me_id=session["user_id"])

@admin_bp.post("/approve/<int:user_id>")
@admin_required
def approve_user(user_id):
    user_to_approve = User.query.get_or_404(user_id)
    if user_to_approve.status == 'pendiente':
        user_to_approve.status = 'activo'
        db.session.commit()
        flash(f"Cuenta de {user_to_approve.name} aprobada.", "success")
    else:
        flash(f"La cuenta de {user_to_approve.name} no estaba pendiente.", "warning")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.post("/reject/<int:user_id>")
@admin_required
def reject_user(user_id):
    user_to_reject = User.query.get_or_404(user_id)
    if user_to_reject.id == session['user_id']:
         flash("No puedes rechazarte a ti mismo.", "danger")
         return redirect(url_for('admin.admin_panel'))

    if user_to_reject.status == 'pendiente':
        db.session.delete(user_to_reject)
        db.session.commit()
        flash(f"Cuenta de {user_to_reject.name} rechazada y borrada.", "info")
    else:
        flash(f"La cuenta de {user_to_reject.name} no estaba pendiente.", "warning")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.post("/delete/<int:user_id>")
@admin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        flash("No puedes borrar tu propia cuenta de administrador.", "danger")
        return redirect(url_for('admin.admin_panel'))

    user_to_delete = User.query.get(user_id)
    if not user_to_delete:
        flash("No se encontró al usuario.", "warning")
        return redirect(url_for('admin.admin_panel'))

    if user_to_delete.username == 'admin':
        flash("La cuenta de super-administrador ('admin') no puede ser borrada.", "danger")
        return redirect(url_for('admin.admin_panel'))

    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"La cuenta de {user_to_delete.name} ha sido borrada permanentemente.", "success")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.post("/promote/<int:user_id>")
@admin_required
def promote_user(user_id):
    me_id = session["user_id"]
    if user_id == me_id:
        flash("No puedes cambiar tu propio rol desde aquí.", "warning")
        return redirect(url_for("admin.admin_panel"))
    u = User.query.get_or_404(user_id)
    u.role = "admin"
    db.session.commit()
    flash(f"{u.name} ahora es administrador.", "success")
    return redirect(url_for("admin.admin_panel"))

@admin_bp.post("/demote/<int:user_id>")
@admin_required
def demote_user(user_id):
    me_id = session["user_id"]
    if user_id == me_id:
        flash("No puedes degradarte a ti mismo desde aquí.", "warning")
        return redirect(url_for("admin.admin_panel"))

    user_to_demote = User.query.get_or_404(user_id)
    if user_to_demote.username == 'admin':
        flash("La cuenta de super-administrador ('admin') no puede ser degradada a usuario.", "danger")
        return redirect(url_for('admin.admin_panel'))

    user_to_demote.role = "user"
    db.session.commit()
    flash(f"{user_to_demote.name} vuelve a ser usuario.", "info")
    return redirect(url_for("admin.admin_panel"))