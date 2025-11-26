import os
from pathlib import Path

class Config:
    SECRET_KEY = "cambia-esto"
    SESSION_PERMANENT = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de la ruta de la BD (se resolverá dinámicamente)
    # Nota: En la fábrica se ajustará la ruta de instance_path si es necesario