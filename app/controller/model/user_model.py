from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.database.connection import db


# Activar Foreign Keys en SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Tabla intermedia Amistades
friendship = db.Table('friendship',
                      db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                      db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
                      )

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    status = db.Column(db.String(20), nullable=False, default='pendiente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones Sociales (Repo 2)
    friends = db.relationship('User',
                              secondary=friendship,
                              primaryjoin=(friendship.c.user_id == id),
                              secondaryjoin=(friendship.c.friend_id == id),
                              backref=db.backref('friend_of', lazy='dynamic'),
                              lazy='dynamic')

    # INTEGRACIÓN REPO 1: Tus equipos
    equipos = db.relationship('Equipo', back_populates='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # "CREACION_EQUIPO", etc.
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Esta relación es necesaria para el dashboard (Changelog)
    # user = db.relationship... (ya debería estar definida en User como backref)