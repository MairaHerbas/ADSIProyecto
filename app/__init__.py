from flask import Flask, render_template
from config import Config
from app.database.connection import db

# Importar Blueprints
from app.controller.ui.auth_controller import auth_bp
from app.controller.ui.pokemon_controller import pokemon_bp
from app.controller.ui.friends import friends_bp
from app.controller.ui.main import main_bp
from app.controller.ui.admin import admin_bp

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

    @app.route('/')
    def index():
        return render_template('index.html')

    with app.app_context():
        # 1. Crear Tablas del Sistema (Usuarios, Amigos, etc.)
        init_tables()

        # 2. Cargar Pokemons si es necesario
        loader = PokemonLoader()
        loader.inicializar_db()
        if loader.db_esta_vacia():
            loader.descargar_datos()

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

    # Tabla EVENT
    db.insert("""
    CREATE TABLE IF NOT EXISTS event (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES user(id)
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

    # Tabla FRIENDSHIP (La que te daba error)
    db.insert("""
    CREATE TABLE IF NOT EXISTS friendship (
        user_id INTEGER,
        friend_id INTEGER,
        PRIMARY KEY (user_id, friend_id),
        FOREIGN KEY(user_id) REFERENCES user(id),
        FOREIGN KEY(friend_id) REFERENCES user(id)
    );
    """)

    # --- EL PRINT QUE PEDISTE ---
    print("\n" + "=" * 50)
    print("✅  API CARGADA CORRECTAMENTE: Tablas inicializadas.")
    print("=" * 50 + "\n")