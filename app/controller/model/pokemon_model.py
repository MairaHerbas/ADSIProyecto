from app.database.connection import db


class Pokemon(db.Model):
    __tablename__ = 'pokemons'  # Plural para coincidir con tu loader
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    imagen_url = db.Column(db.String(255))
    generacion = db.Column(db.Integer)
    tipos = db.Column(db.String(255))
    # ... añade stats si los tienes en tu script loader


class Equipo(db.Model):
    __tablename__ = 'equipo'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nombre_equipo = db.Column(db.String(30), nullable=False)

    user = db.relationship('User', back_populates='equipos')
    pokemons = db.relationship('PokemonEquipo', back_populates='equipo', cascade="all, delete-orphan")


class PokemonEquipo(db.Model):
    __tablename__ = 'pokemon_equipo'
    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id', ondelete='CASCADE'))
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemons.id'))
    orden = db.Column(db.Integer)

    equipo = db.relationship('Equipo', back_populates='pokemons')
    pokemon = db.relationship('Pokemon')