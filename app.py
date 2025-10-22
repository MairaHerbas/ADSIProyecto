from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.engine import Engine
from datetime import datetime
from functools import wraps

# --- CONFIGURACIÓN DE FLASK Y SQLITE ---
app = Flask(__name__, instance_relative_config=True)
Path(app.instance_path).mkdir(parents=True, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(app.instance_path) / 'pokedex.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "cambia-esto"

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
    except Exception:
        pass

db = SQLAlchemy(app)

# --- MODELO DE USUARIO ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # "user" | "admin"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

with app.app_context():
    db.create_all()

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
            return render_template("usuario/welcome_login.html")

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["role"] = user.role
        flash(f"¡Bienvenido/a, {user.name}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("usuario/welcome_login.html")

# --- REGISTRO ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not name or not email or not password or not confirm:
            flash("Rellena todos los campos.", "warning")
            return render_template("usuario/register.html")
        if password != confirm:
            flash("Las contraseñas no coinciden.", "warning")
            return render_template("usuario/register.html")
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "warning")
            return render_template("usuario/register.html")
        if User.query.filter_by(email=email).first():
            flash("Ya existe una cuenta con ese email.", "warning")
            return render_template("usuario/register.html")

        new_user = User(name=name, email=email, role="user")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("home"))

    return render_template("usuario/register.html")

# --- PANEL (DESPUÉS DE LOGIN) ---
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))
    return render_template("usuario/dashboard.html", name=session.get("user_name"), role=session.get("role"))

# --- LOGOUT ---
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("home"))

# --- ADMIN: LISTADO Y PROMOCIÓN/DEGRADACIÓN ---
@app.route("/admin")
@admin_required
def admin():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("usuario/admin.html", users=users, me_id=session["user_id"])

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
    if user_id == me_id:
        flash("No puedes degradarte a ti mismo desde aquí.", "warning")
        return redirect(url_for("admin"))
    u = User.query.get_or_404(user_id)
    u.role = "user"
    db.session.commit()
    flash(f"{u.name} vuelve a ser usuario.", "info")
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
    u = User(name=name, email=email, role="admin")
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    print(f"Admin creado: {email} / {password} (cámbialo luego)")

#--------------------------------------EQUIPO----------------------------------------------------------------------------
# --- MODELO DE POKEMON ---
class Pokemon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    # URL o path a la imagen del Pokémon
    foto_url = db.Column(db.String(255), nullable=False)
    # Cadena de texto o JSON para las estadísticas (ej: 'Ataque: 50, Defensa: 40')
    estadisticas = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Pokemon {self.nombre}>'


# --- MODELO DE EQUIPO ---
class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nombre_equipo = db.Column(db.String(30), nullable=False)

    # Relación uno-a-muchos con la tabla PokemonEquipo
    pokemons = db.relationship('PokemonEquipo', back_populates='equipo', lazy='dynamic', cascade="all, delete-orphan")
    user = db.relationship('User', backref=db.backref('equipos', lazy=True))

    def __repr__(self):
        return f'<Equipo {self.nombre_equipo} de User {self.user_id}>'


# --- TABLA INTERMEDIA para la relación Muchos a Muchos entre Equipo y Pokemon ---
# Un equipo tiene muchos Pokémon, un Pokémon puede estar en muchos equipos.
class PokemonEquipo(db.Model):
    __tablename__ = 'pokemon_equipo'
    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id', ondelete='CASCADE'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), nullable=False)
    # Un equipo no puede tener 2 veces el mismo Pokémon.
    __table_args__ = (db.UniqueConstraint('equipo_id', 'pokemon_id', name='_equipo_pokemon_uc'),)

    # El orden en el equipo (del 1 al 6)
    orden = db.Column(db.Integer, nullable=False)

    equipo = db.relationship('Equipo', back_populates='pokemons')
    pokemon = db.relationship('Pokemon')

    def __repr__(self):
        return f'<PkmnEquipo: E{self.equipo_id} Pk{self.pokemon_id} Ord{self.orden}>'


# Aseguramos que los nuevos modelos se creen en la DB
with app.app_context():
    db.create_all()


# --- FUNCION DE INICIALIZACIÓN (OPCIONAL pero ÚTIL) ---
# Sirve para precargar algunos Pokémon si aún no están en la DB.
# Lo puedes ejecutar con `flask --app app.py init-data`
@app.cli.command("init-data")
def init_data():
    """Carga unos pocos Pokémon y un equipo de prueba: flask --app app.py init-data"""
    # Lista de 6 Pokémon de ejemplo
    pokemon_data = [
        {'nombre': 'Pikachu',
         'foto_url': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png',
         'estadisticas': 'HP: 35, Atk: 55, Def: 40, Spd: 90', 'descripcion': 'Famoso por sus descargas eléctricas.'},
        {'nombre': 'Charmander',
         'foto_url': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/4.png',
         'estadisticas': 'HP: 39, Atk: 52, Def: 43, Spd: 65',
         'descripcion': 'Prefiere los lugares cálidos. Si su cola se apaga, muere.'},
        {'nombre': 'Bulbasaur',
         'foto_url': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png',
         'estadisticas': 'HP: 45, Atk: 49, Def: 49, Spd: 45', 'descripcion': 'Tiene una semilla en su espalda.'},
        {'nombre': 'Squirtle',
         'foto_url': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/7.png',
         'estadisticas': 'HP: 44, Atk: 48, Def: 65, Spd: 43',
         'descripcion': 'Su caparazón sirve para protegerse y nadar.'},
        {'nombre': 'Gengar',
         'foto_url': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/94.png',
         'estadisticas': 'HP: 60, Atk: 65, Def: 60, Spd: 110', 'descripcion': 'Le gusta esconderse en las sombras.'},
        {'nombre': 'Snorlax',
         'foto_url': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/143.png',
         'estadisticas': 'HP: 160, Atk: 110, Def: 65, Spd: 30', 'descripcion': 'Solo come y duerme.'},
    ]

    print("Cargando Pokémon...")
    pokemons = {}
    for data in pokemon_data:
        p = Pokemon.query.filter_by(nombre=data['nombre']).first()
        if not p:
            p = Pokemon(**data)
            db.session.add(p)
        pokemons[p.nombre] = p

    db.session.commit()
    print(f"Pokémon cargados o ya existentes: {len(pokemons)}")

    # Crear equipo de prueba para el primer usuario (si existe)
    user = User.query.first()
    if user and not Equipo.query.filter_by(user_id=user.id).first():
        print(f"Creando Equipo de prueba para {user.name}...")
        equipo = Equipo(user_id=user.id, nombre_equipo="Mi Equipo Inicial")
        db.session.add(equipo)
        db.session.commit()

        # Añadir 6 Pokémon al equipo
        pk_list = list(pokemons.values())
        for i, pk in enumerate(pk_list):
            pk_eq = PokemonEquipo(equipo_id=equipo.id, pokemon_id=pk.id, orden=i + 1)
            db.session.add(pk_eq)

        db.session.commit()
        print(f"Equipo '{equipo.nombre_equipo}' creado y poblado con 6 Pokémon.")
    elif user:
        print(f"El usuario {user.name} ya tiene al menos un equipo. No se crea uno nuevo.")
    else:
        print("No hay usuarios en la base de datos. No se puede crear un equipo.")

    print("Inicialización de datos completada.")
@app.route('/consultar_equipo')
@login_required
def consultar_equipo():
    return render_template('equipo/consultarEquipo.html')


@app.route('/editar_equipo/<int:equipo_id>')
@login_required
def editar_equipo(equipo_id):
    # Lógica para obtener el equipo y verificar permisos.
    equipo = Equipo.query.get_or_404(equipo_id)

    if equipo.user_id != session['user_id']:
        flash("No tienes permiso para editar este equipo.", "danger")
        return redirect(url_for('dashboard'))

    return render_template('equipo/editarEquipo.html', equipo=equipo)

@app.post('/eliminar_equipo/<int:equipo_id>')
@login_required
def eliminar_equipo(equipo_id):
    # 1. Obtener el equipo o 404
    equipo = Equipo.query.get_or_404(equipo_id)

    # 2. Asegurarse de que el equipo pertenece al usuario logueado
    if equipo.user_id != session['user_id']:
        flash("No tienes permiso para eliminar este equipo.", "danger")
        return redirect(url_for('dashboard'))

    # 3. Eliminar el equipo. La configuración de `cascade="all, delete-orphan"`
    # y `ondelete='CASCADE'` en los modelos se encarga de eliminar también
    # las entradas de la tabla intermedia `PokemonEquipo`.
    db.session.delete(equipo)
    db.session.commit()

    flash(f"El equipo '{equipo.nombre_equipo}' ha sido eliminado.", "success")
    return redirect(url_for('principal.html'))
if __name__ == "__main__":
    app.run(debug=True)