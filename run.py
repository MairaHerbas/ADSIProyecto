from pathlib import Path
from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

if __name__ == "__main__":
    # Lógica de creación inicial de la BD
    db_file = Path(app.instance_path) / 'pokedex.db'
    
    with app.app_context():
        if not db_file.exists():
            print("Base de datos no encontrada. Creando tablas y admin...")
            db.create_all()

            admin_email = "admin@demo.com"
            admin_pass = "admin123"
            admin_user = User(
                name="Admin",
                username="admin",
                email=admin_email,
                role="admin",
                status="activo"
            )
            admin_user.set_password(admin_pass)
            db.session.add(admin_user)
            db.session.commit()
            print(f"¡Base de datos y admin '{admin_email}' creados con éxito!")
        else:
            print("Base de datos encontrada. Iniciando aplicación.")

    app.run(debug=True)