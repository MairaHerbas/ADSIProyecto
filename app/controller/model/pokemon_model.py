from datetime import datetime
from app.database.connection import db


class Pokemon(db.Model):
    __tablename__ = 'pokemons'

    # --- LAS 13 COLUMNAS EXACTAS QUE USA TU CARGADOR ---
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    imagen_url = db.Column(db.String(255))  # Ojo: asegúrate de llamarlo igual que en tu script loader
    generacion = db.Column(db.Integer)
    altura = db.Column(db.Float)
    peso = db.Column(db.Float)
    tipos = db.Column(db.String(255))
    habilidades = db.Column(db.String(255))
    movimientos = db.Column(db.String(255))
    hp = db.Column(db.Integer)
    ataque = db.Column(db.Integer)
    defensa = db.Column(db.Integer)
    velocidad = db.Column(db.Integer)

    def __repr__(self):
        return f'<Pokemon {self.nombre}>'


class Equipo(db.Model):
    __tablename__ = 'equipo'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nombre_equipo = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='equipos')
    pokemons = db.relationship('PokemonEquipo', back_populates='equipo', cascade="all, delete-orphan")


class PokemonEquipo(db.Model):
    __tablename__ = 'pokemon_equipo'
    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id', ondelete='CASCADE'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemons.id'), nullable=False)

    # Datos extra exigidos por tus diagramas
    orden = db.Column(db.Integer, nullable=False)
    apodo = db.Column(db.String(50), nullable=True)
    habilidad = db.Column(db.String(50), nullable=True)
    movimiento = db.Column(db.String(50), nullable=True)
    fecha_captura = db.Column(db.DateTime, default=datetime.utcnow)

    equipo = db.relationship('Equipo', back_populates='pokemons')
    pokemon = db.relationship('Pokemon')