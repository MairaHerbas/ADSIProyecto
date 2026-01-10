from flask import Flask
from config import Config
from app.database.connection import db

# Importar Blueprints
from app.controller.ui.auth_controller import auth_bp
from app.controller.ui.pokemon_controller import pokemon_bp
# Importa aquí admin_bp, friends_bp, main_bp cuando crees sus archivos

# Importar Loader
from app.services.pokemon_loader import PokemonLoader


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar DB
    db.init_app(app)

    # Registrar Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(pokemon_bp)
    # app.register_blueprint(admin_bp)
    # app.register_blueprint(friends_bp)
    # app.register_blueprint(main_bp)

    with app.app_context():
        # Crea tablas si no existen
        db.create_all()

        # Carga inicial de datos si la DB está vacía
        loader = PokemonLoader()
        loader.inicializar_db()  # Crea tabla pokemons si no existe
        if loader.db_esta_vacia():
            loader.descargar_datos()

    return app