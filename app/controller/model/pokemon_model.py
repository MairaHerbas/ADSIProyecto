from datetime import datetime
from app.database.connection import db


class Pokemon(db.Model):
    __tablename__ = 'pokemons'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    imagen_url = db.Column(db.String(255))
    generacion = db.Column(db.Integer)
    tipos = db.Column(db.String(255))

    # Agrega stats si los necesitas

    def __repr__(self):
        return f'<Pokemon {self.nombre}>'


class Equipo(db.Model):
    __tablename__ = 'equipo'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nombre_equipo = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Útil para ordenar

    user = db.relationship('User', back_populates='equipos')
    # Cascade all, delete-orphan asegura que si borras equipo, se borran los links a pokemon
    pokemons = db.relationship('PokemonEquipo', back_populates='equipo', cascade="all, delete-orphan")


class PokemonEquipo(db.Model):
    __tablename__ = 'pokemon_equipo'
    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id', ondelete='CASCADE'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemons.id'), nullable=False)

    # --- CAMPOS EXIGIDOS POR EL DIAGRAMA DE CONSULTA ---
    orden = db.Column(db.Integer, nullable=False)
    apodo = db.Column(db.String(50), nullable=True)  # Nodo 3.2.1
    habilidad = db.Column(db.String(50), nullable=True)  # Nodo 3.2.2
    movimiento = db.Column(db.String(50), nullable=True)  # Nodo 3.2.3
    fecha_captura = db.Column(db.DateTime, default=datetime.utcnow)  # Nodo 3.2.4

    equipo = db.relationship('Equipo', back_populates='pokemons')
    pokemon = db.relationship('Pokemon')

