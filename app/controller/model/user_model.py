from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.connection import db


# --- CLASE USER ---
class User:
    def __init__(self, id, name, username, email, password_hash, role, status, created_at):
        self.id = id
        self.name = name
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.status = status
        self.created_at = created_at

    # --- SQL: Búsquedas ---
    @staticmethod
    def get_by_email(email):
        row = db.select("SELECT * FROM user WHERE email = ?", (email,))
        return User(**dict(row[0])) if row else None

    @staticmethod
    def filter_users(status=None, search=None):
        # Excluir admins para seguridad
        query = "SELECT * FROM user WHERE role != 'admin'"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if search:
            query += " AND (username LIKE ? OR name LIKE ?)"
            term = f"%{search}%"
            params.append(term)
            params.append(term)

        query += " ORDER BY created_at DESC"

        rows = db.select(query, tuple(params))
        return [User(**dict(r)) for r in rows]

    @staticmethod
    def update_status(user_id, new_status):
        return db.update("UPDATE user SET status = ? WHERE id = ?", (new_status, user_id))
    @staticmethod
    def get_by_id(user_id):
        row = db.select("SELECT * FROM user WHERE id = ?", (user_id,))
        return User(**dict(row[0])) if row else None

    @staticmethod
    def get_by_username(username):
        row = db.select("SELECT * FROM user WHERE username = ?", (username,))
        return User(**dict(row[0])) if row else None

    @staticmethod
    def get_all_excluding(user_id):
        rows = db.select("SELECT * FROM user WHERE id != ?", (user_id,))
        return [User(**dict(r)) for r in rows]

    @staticmethod
    def create(name, username, email, password, role='user', status='pendiente'):
            """
            Crea un usuario. Por defecto role='user' y status='pendiente'
            para el sistema de aprobación.
            """
            hashed_pw = generate_password_hash(password)
            created_at = datetime.utcnow()

            sql = """
                  INSERT INTO user (name, username, email, password_hash, role, status, created_at)
                  VALUES (?, ?, ?, ?, ?, ?, ?) \
                  """
            # Ahora pasamos 'role' y 'status' dinámicamente en lugar de escribirlos fijos
            return db.insert(sql, (name, username, email, hashed_pw, role, status, created_at))


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    # --- Propiedades de Relación ---
    @property
    def friends(self):
        sql = """
            SELECT u.* FROM user u
            JOIN friendship f ON (u.id = f.friend_id OR u.id = f.user_id)
            WHERE (f.user_id = ? OR f.friend_id = ?) AND u.id != ?
        """
        rows = db.select(sql, (self.id, self.id, self.id))
        return [User(**dict(r)) for r in rows]

    @property
    def equipos(self):
        # Importación local para evitar ciclos
        from app.controller.model.team_model import Equipo
        return Equipo.get_by_user(self.id)

    @staticmethod
    def delete(user_id):
        """Borra un usuario permanentemente de la base de datos"""
        return db.delete("DELETE FROM user WHERE id = ?", (user_id,))

    @staticmethod
    def update_role(user_id, new_role):
        """Actualiza el rol del usuario ('admin' o 'user')"""
        return db.update("UPDATE user SET role = ? WHERE id = ?", (new_role, user_id))

    # --- AÑADIR EN LA CLASE USER (user_model.py) ---

    @staticmethod
    def get_friendship_candidates(user_id):
        """
        Devuelve lista de usuarios que NO son amigos ni tienen peticiones pendientes.
        """
        # Esta query selecciona el username de todos los usuarios...
        # ...excluyendo al propio usuario
        # ...excluyendo amigos confirmados (tabla friendship)
        # ...excluyendo solicitudes pendientes (tabla friend_request)

        sql = """
              SELECT username \
              FROM user
              WHERE id != ?
            AND status = 'aprobado'  -- Solo usuarios activos (opcional)
            AND id NOT IN (
                SELECT friend_id FROM friendship WHERE user_id = ?
                UNION
                SELECT user_id FROM friendship WHERE friend_id = ?
            )
            AND id NOT IN (
                SELECT receiver_id FROM friend_request 
                WHERE sender_id = ? AND status = 'pending'
            )
            AND id NOT IN (
                SELECT sender_id FROM friend_request 
                WHERE receiver_id = ? AND status = 'pending'
            ) \
              """
        # Pasamos el user_id 5 veces porque hay 5 ? en la consulta
        rows = db.select(sql, (user_id, user_id, user_id, user_id, user_id))

        # Devolvemos una lista simple de nombres: ['Ash', 'Misty', 'Brock']
        return [r['username'] for r in rows]

# --- CLASE EVENT (Esta es la que te faltaba) ---
# --- CLASE EVENT (Actualizada) ---
class Event:
    def __init__(self, id, user_id, event_type, description, created_at):
        self.id = id
        self.user_id = user_id
        self.event_type = event_type
        self.description = description
        self.created_at = created_at

    @staticmethod
    def create(user_id, event_type, description):
        created_at = datetime.utcnow()
        sql = "INSERT INTO event (user_id, event_type, description, created_at) VALUES (?, ?, ?, ?)"
        db.insert(sql, (user_id, event_type, description, created_at))

    @staticmethod
    def get_recent_by_users(user_ids_list, limit=50):
        if not user_ids_list:
            return []

        # Crear placeholders dinámicos (?, ?, ?) según cantidad de IDs
        placeholders = ','.join(['?'] * len(user_ids_list))
        sql = f"""
            SELECT * FROM event 
            WHERE user_id IN ({placeholders}) 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        # Añadimos el límite al final de los argumentos
        args = list(user_ids_list) + [limit]

        rows = db.select(sql, tuple(args))
        # Devolvemos objetos Event para que el HTML los entienda (event.description)
        return [Event(**dict(r)) for r in rows]

# --- CLASE FRIEND REQUEST ---
class FriendRequest:
    def __init__(self, id, sender_id, receiver_id, status, created_at, sender_name=None):
        self.id = id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.status = status
        self.created_at = created_at
        self.sender_name = sender_name

    @staticmethod
    def create(sender_id, receiver_id):
        created_at = datetime.utcnow()
        sql = "INSERT INTO friend_request (sender_id, receiver_id, status, created_at) VALUES (?, ?, 'pending', ?)"
        db.insert(sql, (sender_id, receiver_id, created_at))

    @staticmethod
    def get_existing(sender_id, receiver_id):
        sql = """
            SELECT * FROM friend_request 
            WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
            AND status = 'pending'
        """
        rows = db.select(sql, (sender_id, receiver_id, receiver_id, sender_id))
        return rows[0] if rows else None

    @staticmethod
    def get_received_pending(user_id):
        sql = """
            SELECT fr.*, u.username as sender_name 
            FROM friend_request fr
            JOIN user u ON fr.sender_id = u.id
            WHERE fr.receiver_id = ? AND fr.status = 'pending'
        """
        rows = db.select(sql, (user_id,))
        requests = []
        for r in rows:
            d = dict(r)
            requests.append(FriendRequest(d['id'], d['sender_id'], d['receiver_id'], d['status'], d['created_at'],
                                          d['sender_name']))
        return requests

    @staticmethod
    def accept(request_id):
        db.update("UPDATE friend_request SET status = 'accepted' WHERE id = ?", (request_id,))
        rows = db.select("SELECT sender_id, receiver_id FROM friend_request WHERE id = ?", (request_id,))
        if rows:
            req = dict(rows[0])
            db.insert("INSERT INTO friendship (user_id, friend_id) VALUES (?, ?)",
                      (req['sender_id'], req['receiver_id']))

    @staticmethod
    def reject(request_id):
        db.delete("DELETE FROM friend_request WHERE id = ?", (request_id,))

    @staticmethod
    def remove_friend(user_id, friend_id):
        sql = """
            DELETE FROM friendship 
            WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)
        """
        db.delete(sql, (user_id, friend_id, friend_id, user_id))