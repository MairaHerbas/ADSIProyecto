from flask import Flask
from pathlib import Path
from .extensions import db
from .models import User
from config import Config

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Cargar configuración
    app.config.from_object(Config)
    
    # Ajuste de ruta BD
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(app.instance_path) / 'pokedex.db'}"

    # Iniciar extensiones
    db.init_app(app)

    # Registrar Blueprints (Rutas)
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.friends import friends_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(admin_bp)

    # --- CLI COMMANDS ---
    @app.cli.command("create-admin")
    def create_admin():
        """Crea un admin rápido: flask --app run.py create-admin"""
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
        print(f"Admin creado: {email} / {password}")

    return app