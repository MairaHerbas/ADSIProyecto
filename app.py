from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.engine import Engine
from datetime import datetime
from functools import wraps
import os

# --- CONFIGURACIÓN DE FLASK Y SQLITE ---
app = Flask(__name__, instance_relative_config=True)
Path(app.instance_path).mkdir(parents=True, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(app.instance_path) / 'pokedex.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "cambia-esto"
app.config["SESSION_PERMANENT"] = False

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
    except Exception:
        pass

db = SQLAlchemy(app)


# --- TABLA DE ASOCIACIÓN PARA AMISTADES (Muchos-a-Muchos) ---
# Esta tabla solo guarda pares de IDs (amigo1, amigo2)
friendship = db.Table('friendship',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)
# --- MODELO DE USUARIO ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # "user" | "admin"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Por defecto, 'pendiente' cuando se crea
    status = db.Column(db.String(20), nullable=False, default='pendiente')
    # Define la relación de muchos-a-muchos
    friends = db.relationship('User',
                              secondary=friendship,
                              primaryjoin=(friendship.c.user_id == id),
                              secondaryjoin=(friendship.c.friend_id == id),
                              backref=db.backref('friend_of', lazy='dynamic'),
                              lazy='dynamic')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') # pending, accepted, declined

    # Relaciones para poder acceder a los objetos User
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')

# --- HELPERS DE AUTORIZACIÓN ---
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapper

def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("home"))
        if session.get("role") != "admin":
            flash("No tienes permisos para acceder a Admin.", "danger")
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapper

def get_current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])

# --- HOME = Bienvenida + Login ---
@app.route("/", methods=["GET", "POST"])
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
            return redirect(url_for("dashboard"))
        elif user.status == 'pendiente':
            flash('Tu cuenta todavía no ha sido aprobada por un administrador.', 'warning')
            return render_template("welcome_login.html")

        else:
            # Estado desconocido o no permitido para login
            flash('Hay un problema con el estado de tu cuenta. Contacta al administrador.', 'danger')
            return render_template("welcome_login.html")


    return render_template("welcome_login.html")

# --- REGISTRO ---
@app.route("/register", methods=["GET", "POST"])
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
        return redirect(url_for("home"))

    return render_template("register.html")

# --- PANEL (DESPUÉS DE LOGIN) ---
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard.html", name=session.get("user_name"), role=session.get("role"))

@app.route("/amistades")
@login_required  # Requiere estar logueado
def gestionar_amistades():
    # Por ahora, solo muestra la página.
    return render_template("amistades.html")


# --- RUTA PARA BUSCAR AMIGOS (NUEVA) ---
@app.route("/amistades/buscar", methods=["GET", "POST"])
@login_required
def buscar_amigos():
    resultado_busqueda = None
    query = None

    if request.method == "POST":
        query = request.form.get("username_busqueda", "").strip().lower()

        if not query:
            flash("Por favor, introduce un nombre de usuario para buscar.", "warning")
            return redirect(url_for('buscar_amigos'))

        # Buscamos al usuario
        resultado_busqueda = User.query.filter_by(username=query).first()

        # Comprobación 1: No puedes buscarte a ti mismo
        if resultado_busqueda and resultado_busqueda.id == session['user_id']:
            flash("No puedes enviarte una solicitud a ti mismo.", "warning")
            resultado_busqueda = None  # Anulamos el resultado

    # GET (o después de un POST): Renderiza la plantilla con los resultados
    # resultado_busqueda será None si es GET, si no se encontró, o si eres tú mismo
    # query tendrá el término de búsqueda si fue un POST
    return render_template("buscar_amigos.html",
                           resultado=resultado_busqueda,
                           query=query)


# --- RUTA PARA ENVIAR SOLICITUD (Placeholder) ---
@app.post("/amistades/enviar/<int:user_id>")
@login_required
def enviar_solicitud(user_id):
    receiver = User.query.get_or_404(user_id)
    sender = get_current_user()  # (Necesitamos la función get_current_user que ya tenías)

    # --- VALIDACIONES ---
    # No puedes enviarte a ti mismo (ya lo validamos en la búsqueda, pero por si acaso)
    if receiver.id == sender.id:
        flash("No puedes enviarte una solicitud a ti mismo.", "warning")
        return redirect(url_for('buscar_amigos'))

    # Ya son amigos
    if sender.friends.filter(friendship.c.friend_id == receiver.id).count() > 0:
        flash(f"Ya eres amigo de {receiver.username}.", "info")
        return redirect(url_for('buscar_amigos'))

    # Ya existe una solicitud pendiente (de él hacia ti o de ti hacia él)
    existing_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == sender.id) & (FriendRequest.receiver_id == receiver.id)) |
        ((FriendRequest.sender_id == receiver.id) & (FriendRequest.receiver_id == sender.id))
    ).filter(FriendRequest.status == 'pending').first()

    if existing_request:
        flash("Ya hay una solicitud de amistad pendiente con este usuario.", "warning")
        return redirect(url_for('buscar_amigos'))

    # --- CREAR SOLICITUD ---
    new_request = FriendRequest(sender_id=sender.id, receiver_id=receiver.id)
    db.session.add(new_request)
    db.session.commit()

    flash(f"¡Solicitud de amistad enviada a {receiver.username}!", "success")
    return redirect(url_for('buscar_amigos'))


@app.route("/amistades/solicitudes")
@login_required
def ver_solicitudes():
    current_user_id = session['user_id']

    # Buscamos todas las solicitudes PENDIENTES donde YO soy el RECEPTOR
    solicitudes = FriendRequest.query.filter_by(
        receiver_id=current_user_id,
        status='pending'
    ).order_by(FriendRequest.created_at.desc()).all()

    return render_template("solicitudes_recibidas.html", solicitudes=solicitudes)


@app.post("/amistades/aceptar/<int:request_id>")
@login_required
def aceptar_solicitud(request_id):
    solicitud = FriendRequest.query.get_or_404(request_id)

    # Seguridad: solo el receptor puede aceptar
    if solicitud.receiver_id != session['user_id']:
        abort(403)  # Error de "Prohibido"

    # 1. Actualiza el estado de la solicitud
    solicitud.status = 'accepted'

    # 2. Creamos la amistad (bidireccional)
    usuario_actual = get_current_user()
    nuevo_amigo = solicitud.sender

    usuario_actual.friends.append(nuevo_amigo)
    nuevo_amigo.friends.append(usuario_actual)

    db.session.commit()

    flash(f"¡Ahora eres amigo de {nuevo_amigo.username}!", "success")
    return redirect(url_for('ver_solicitudes'))


@app.post("/amistades/rechazar/<int:request_id>")
@login_required
def rechazar_solicitud(request_id):
    solicitud = FriendRequest.query.get_or_404(request_id)

    # Seguridad: solo el receptor puede rechazar
    if solicitud.receiver_id != session['user_id']:
        abort(403)

    # Opción 1: Marcar como 'declined'
    # solicitud.status = 'declined'
    # db.session.commit()

    # Opción 2: Borrarla (más limpio)
    db.session.delete(solicitud)
    db.session.commit()

    flash(f"Solicitud de {solicitud.sender.username} rechazada.", "info")
    return redirect(url_for('ver_solicitudes'))


# --- RUTA PARA VER LA LISTA DE AMIGOS  ---
@app.route("/amistades/lista")
@login_required
def ver_amigos():
    # 1. Obtenemos el objeto del usuario actual
    current_user = get_current_user()

    # 2. Gracias a la magia de SQLAlchemy (secondary=friendship),
    #    podemos pedirle directamente su lista de .friends
    #    La ordenamos por nombre de usuario para que se vea bien.
    lista_amigos = current_user.friends.order_by(User.username).all()

    # 3. Le pasamos la lista de objetos User directamente a la plantilla
    return render_template("ver_amigos.html", lista_amigos=lista_amigos)


# --- RUTA PARA ELIMINAR UN AMIGO (NUEVA) ---
@app.post("/amistades/eliminar/<int:friend_id>")
@login_required
def eliminar_amigo(friend_id):
    # Obtenemos al usuario actual
    current_user = get_current_user()

    # Obtenemos al amigo que queremos borrar
    friend_to_remove = User.query.get_or_404(friend_id)

    # Lógica de borrado bidireccional:
    # SQLAlchemy es lo bastante inteligente para ir a la tabla 'friendship'
    # y borrar la fila que conecta a estos dos usuarios.

    # 1. Te borro a él de mi lista
    current_user.friends.remove(friend_to_remove)

    # 2. Le borro a él de tu lista
    friend_to_remove.friends.remove(current_user)

    # Guardamos los cambios
    db.session.commit()

    flash(f"Has eliminado a {friend_to_remove.username} de tu lista de amigos.", "info")
    return redirect(url_for('ver_amigos'))  # Volvemos a la lista de amigos
# --- LOGOUT ---
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("home"))

@app.post("/admin/approve/<int:user_id>")
@admin_required
def approve_user(user_id):
    user_to_approve = User.query.get_or_404(user_id)
    if user_to_approve.status == 'pendiente':
        user_to_approve.status = 'activo'
        db.session.commit()
        flash(f"Cuenta de {user_to_approve.name} aprobada.", "success")
    else:
        flash(f"La cuenta de {user_to_approve.name} no estaba pendiente.", "warning")
    return redirect(url_for('admin'))

@app.post("/admin/reject/<int:user_id>")
@admin_required
def reject_user(user_id):
    user_to_reject = User.query.get_or_404(user_id)
    if user_to_reject.id == session['user_id']:
         flash("No puedes rechazarte a ti mismo.", "danger")
         return redirect(url_for('admin'))

    if user_to_reject.status == 'pendiente':
        # Opción 1: Borrar directamente
        db.session.delete(user_to_reject)
        db.session.commit()
        flash(f"Cuenta de {user_to_reject.name} rechazada y borrada.", "info")
        # Opción 2: Marcar como rechazado (necesitarías añadir ese estado al modelo)
        # user_to_reject.status = 'rechazado'
        # db.session.commit()
        # flash(f"Cuenta de {user_to_reject.name} marcada como rechazada.", "info")
    else:
        flash(f"La cuenta de {user_to_reject.name} no estaba pendiente.", "warning")
    return redirect(url_for('admin'))


@app.post("/admin/delete/<int:user_id>")
@admin_required
def delete_user(user_id):
    # Comprobación de seguridad 1: No te puedes borrar a ti mismo
    if user_id == session['user_id']:
        flash("No puedes borrar tu propia cuenta de administrador.", "danger")
        return redirect(url_for('admin'))

    # Busca al usuario en la base de datos
    user_to_delete = User.query.get(user_id)

    if not user_to_delete:
        flash("No se encontró al usuario.", "warning")
        return redirect(url_for('admin'))

    # --- ¡NUEVA COMPROBACIÓN DE SEGURIDAD 2! ---
    # No se puede borrar al super-administrador (el que tiene username 'admin')
    if user_to_delete.username == 'admin':
        flash("La cuenta de super-administrador ('admin') no puede ser borrada.", "danger")
        return redirect(url_for('admin'))
    # --- FIN DE LA NUEVA COMPROBACIÓN ---

    # Si pasa ambas comprobaciones, borra al usuario
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"La cuenta de {user_to_delete.name} ha sido borrada permanentemente.", "success")

    return redirect(url_for('admin'))

# --- ADMIN: LISTADO Y PROMOCIÓN/DEGRADACIÓN ---
@app.route("/admin")
@admin_required
def admin():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin.html", users=users, me_id=session["user_id"])

@app.post("/admin/promote/<int:user_id>")
@admin_required
def promote_user(user_id):
    me_id = session["user_id"]
    if user_id == me_id:
        flash("No puedes cambiar tu propio rol desde aquí.", "warning")
        return redirect(url_for("admin"))
    u = User.query.get_or_404(user_id)
    u.role = "admin"
    db.session.commit()
    flash(f"{u.name} ahora es administrador.", "success")
    return redirect(url_for("admin"))


@app.post("/admin/demote/<int:user_id>")
@admin_required
def demote_user(user_id):
    me_id = session["user_id"]

    # Comprobación de seguridad 1: No puedes degradarte a ti mismo
    if user_id == me_id:
        flash("No puedes degradarte a ti mismo desde aquí.", "warning")
        return redirect(url_for("admin"))

    # Busca al usuario
    user_to_demote = User.query.get_or_404(user_id)

    # --- ¡NUEVA COMPROBACIÓN DE SEGURIDAD 2! ---
    # No se puede degradar al super-administrador (el que tiene username 'admin')
    if user_to_demote.username == 'admin':
        flash("La cuenta de super-administrador ('admin') no puede ser degradada a usuario.", "danger")
        return redirect(url_for('admin'))
    # --- FIN DE LA NUEVA COMPROBACIÓN ---

    # Si pasa ambas comprobaciones, degrada al usuario
    user_to_demote.role = "user"
    db.session.commit()
    flash(f"{user_to_demote.name} vuelve a ser usuario.", "info")
    return redirect(url_for("admin"))

# --- CLI: crear un admin “a mano” ---
@app.cli.command("create-admin")
def create_admin():
    """Crea un admin rápido: flask --app app.py create-admin"""
    email = "admin@demo.com"
    name = "Admin"
    password = "admin123"
    if User.query.filter_by(email=email).first():
        print("Ya existe:", email)
        return
    u = User(name=name, email=email, username=email, role="admin", status="activo")
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    print(f"Admin creado: {email} / {password} (cámbialo luego)")

    # --- EDITAR PERFIL (USUARIO O ADMIN) ---
@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
        user = get_current_user()
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            confirm = request.form.get("confirm") or ""

            # Validaciones básicas
            if not name or not email:
                flash("El nombre y el email son obligatorios.", "warning")
                return render_template("profile_edit.html", user=user)

            # Evita duplicar email de otro usuario
            existing = User.query.filter(User.email == email, User.id != user.id).first()
            if existing:
                flash("Ya existe otro usuario con ese email.", "warning")
                return render_template("profile_edit.html", user=user)

            # Cambio de contraseña (opcional)
            if password:
                if password != confirm:
                    flash("Las contraseñas no coinciden.", "warning")
                    return render_template("profile_edit.html", user=user)
                if len(password) < 6:
                    flash("La contraseña debe tener al menos 6 caracteres.", "warning")
                    return render_template("profile_edit.html", user=user)
                user.set_password(password)

            # Actualiza nombre y email
            user.name = name
            user.email = email
            db.session.commit()

            # Actualiza la sesión para mostrar el nuevo nombre
            session["user_name"] = user.name

            flash("Datos actualizados correctamente.", "success")
            return redirect(url_for("dashboard"))

        # GET: mostrar el formulario con datos actuales
        return render_template("profile_edit.html", user=user)


if __name__ == "__main__":

    # Definimos la ruta a la BD, igual que en tu config
    db_file = Path(app.instance_path) / 'pokedex.db'

    # Usamos el contexto de la app para todas las operaciones de BD
    with app.app_context():

        # 1. Comprueba si la BD NO existe
        if not db_file.exists():
            print("Base de datos no encontrada. Creando tablas y admin...")

            # 2. Crea todas las tablas
            db.create_all()

            # 3. Crea el usuario admin (misma lógica de tu comando 'create-admin')
            admin_email = "admin@demo.com"
            admin_pass = "admin123"

            admin_user = User(
                name="Admin",
                username="admin",
                email=admin_email,
                role="admin",
                status="activo"  # ¡Importante! Lo ponemos 'activo' de inmediato
            )
            admin_user.set_password(admin_pass)

            db.session.add(admin_user)
            db.session.commit()
            print(f"¡Base de datos y admin '{admin_email}' creados con éxito!")

        else:
            print("Base de datos encontrada. Iniciando aplicación.")

    # 4. Ejecuta la aplicación (igual que tu línea original)
    app.run(debug=True)
