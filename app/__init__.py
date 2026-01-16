from flask import Flask, render_template
from config import Config
from app.database.connection import db

# Importar Blueprints existentes
from app.controller.ui.auth_controller import auth_bp
from app.controller.ui.pokemon_controller import pokemon_bp
from app.controller.ui.friends import friends_bp
from app.controller.ui.main import main_bp
from app.controller.ui.admin import admin_bp
from app.controller.ui.team_controller import team_bp

from app.controller.ui.routes_changelog import changelog_bp

# Importar Loader
from app.services.pokemon_loader import PokemonLoader


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registrar Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(pokemon_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(changelog_bp)
    app.register_blueprint(team_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    with app.app_context():
        # 1. PRIMERO: Cargar Pokemons (Crea la tabla 'pokemons' y descarga datos si hace falta)
        # Es importante hacerlo antes de init_tables para que la tabla 'pokemons' exista
        # cuando 'pokemon_equipo' intente referenciarla.
        loader = PokemonLoader()
        loader.descargar_datos()  # <--- ESTA ES LA ÚNICA LLAMADA NECESARIA

        # 2. SEGUNDO: Crear resto de tablas del Sistema
        init_tables()

    return app


def init_tables():
    """Crea las tablas del sistema manualmente con SQL puro."""

    # Tabla USER
    db.insert("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        status TEXT DEFAULT 'pendiente',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabla EQUIPO
    db.insert("""
    CREATE TABLE IF NOT EXISTS equipo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        nombre_equipo TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES user(id)
    );
    """)

    # Tabla POKEMON_EQUIPO
    db.insert("""
    CREATE TABLE IF NOT EXISTS pokemon_equipo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipo_id INTEGER NOT NULL,
        pokemon_id INTEGER NOT NULL,
        orden INTEGER NOT NULL,
        apodo TEXT,
        habilidad TEXT,
        movimiento TEXT,
        fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(equipo_id) REFERENCES equipo(id) ON DELETE CASCADE,
        FOREIGN KEY(pokemon_id) REFERENCES pokemons(id)
    );
    """)

    # Tabla FRIEND_REQUEST
    db.insert("""
    CREATE TABLE IF NOT EXISTS friend_request (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(sender_id) REFERENCES user(id),
        FOREIGN KEY(receiver_id) REFERENCES user(id)
    );
    """)

    # Tabla FRIENDSHIP
    db.insert("""
    CREATE TABLE IF NOT EXISTS friendship (
        user_id INTEGER,
        friend_id INTEGER,
        PRIMARY KEY (user_id, friend_id),
        FOREIGN KEY(user_id) REFERENCES user(id),
        FOREIGN KEY(friend_id) REFERENCES user(id)
    );
    """)

    # Tabla CHANGELOG_EVENT
    db.insert("""
    CREATE TABLE IF NOT EXISTS Changelog_Event (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idUsuario INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        fecha DATETIME DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(idUsuario) REFERENCES user(id)
    );
    """)

    print("\n" + "=" * 50)
    print("✅  API CARGADA CORRECTAMENTE: Tablas inicializadas.")
    print("=" * 50 + "\n")