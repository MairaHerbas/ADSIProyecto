import os

class Config:
    SECRET_KEY = "123"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    # Ruta absoluta para evitar problemas
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'pokedex.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False