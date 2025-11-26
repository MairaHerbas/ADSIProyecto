from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy.engine import Engine
from .extensions import db


# --- EVENTO SQLITE (PRAGMA) ---
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
    except Exception:
        pass

# --- TABLA DE ASOCIACIÓN ---
friendship = db.Table('friendship',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# --- MODELO USER ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pendiente')
    
    friends = db.relationship('User',
                              secondary=friendship,
                              primaryjoin=(friendship.c.user_id == id),
                              secondaryjoin=(friendship.c.friend_id == id),
                              backref=db.backref('friend_of', lazy='dynamic'),
                              lazy='dynamic')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

# --- MODELO FRIEND REQUEST ---
class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Tipo de evento: 'CAPTURA', 'EQUIPO_CREADO', 'EQUIPO_EDITADO', etc.
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación para saber quién generó el evento
    user = db.relationship('User', backref=db.backref('events', lazy=True))

