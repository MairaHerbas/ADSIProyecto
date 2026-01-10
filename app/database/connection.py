from flask_sqlalchemy import SQLAlchemy

# Inicializamos la base de datos vacía.
# Se conectará a la app más tarde en el __init__.py
db = SQLAlchemy()