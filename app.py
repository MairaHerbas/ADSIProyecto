import os, sqlite3, secrets, hashlib, hmac
from datetime import datetime
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, abort

# ---------------------- CONFIG ----------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-" + secrets.token_hex(16)  # cambia en producción
DB_PATH = os.path.join(os.path.dirname(__file__), "pokedex.db")
PBKDF_ITERATIONS = 240_000
SALT_LEN = 16

# ---------------------- DB HELPERS -------------------
def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_schema():
    db = get_db()
    db.executescript("""
    PRAGMA foreign_keys=ON;

    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      display_name TEXT NOT NULL,
      bio TEXT DEFAULT '',
      is_admin INTEGER DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'PENDING',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS credentials(
      user_id INTEGER PRIMARY KEY,
      salt BLOB NOT NULL,
      pw_hash BLOB NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS follows(
      follower_id INTEGER NOT NULL,
      followed_id INTEGER NOT NULL,
      created_at TEXT NOT NULL,
      PRIMARY KEY(follower_id, followed_id),
      FOREIGN KEY(follower_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY(followed_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    db.commit()

    # seed admin si no existe
    cur = db.execute("SELECT id FROM users WHERE email=?", ("admin@pokedex.local",))
    if not cur.fetchone():
        now = datetime.utcnow().isoformat()
        db.execute(
            "INSERT INTO users(email, display_name, bio, is_admin, status, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?)",
            ("admin@pokedex.local", "Administrador", "", 1, "APPROVED", now, now),
        )
        uid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        salt, h = hash_password("admin123")
        db.execute("INSERT INTO credentials(user_id, salt, pw_hash) VALUES(?,?,?)", (uid, salt, h))
        db.commit()

# ---------------------- PASSWORDS --------------------
def hash_password(password: str):
    salt = secrets.token_bytes(SALT_LEN)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF_ITERATIONS)
    return salt, dk

def verify_password(password: str, salt: bytes, stored_dk: bytes) -> bool:
    cand = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF_ITERATIONS)
    return hmac.compare_digest(cand, stored_dk)

# ---------------------- AUTH DECORATORS --------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            abort(403)
        return f(*args, **kwargs)
    return wrapper

# ---------------------- HELPERS ----------------------
def current_user():
    if "user_id" not in session:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()

# ---------------------- ROUTES -----------------------
@app.before_request
def _ensure_db():
    # asegura que el schema esté listo
    if not os.path.exists(DB_PATH):
        open(DB_PATH, "a").close()
    init_schema()

@app.route("/")
def index():
    return render_template("index.html", me=current_user())

# --------- Registro ---------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        name  = (request.form.get("display_name") or "").strip()
        pw1   = request.form.get("password") or ""
        pw2   = request.form.get("password2") or ""
        if not email or not name or not pw1:
            flash("Rellena todos los campos.", "error")
        elif pw1 != pw2:
            flash("Las contraseñas no coinciden.", "error")
        else:
            db = get_db()
            try:
                now = datetime.utcnow().isoformat()
                db.execute(
                    "INSERT INTO users(email, display_name, bio, is_admin, status, created_at, updated_at) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (email, name, "", 0, "PENDING", now, now)
                )
                uid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                salt, h = hash_password(pw1)
                db.execute("INSERT INTO credentials(user_id, salt, pw_hash) VALUES(?,?,?)", (uid, salt, h))
                db.commit()
                flash("Cuenta creada. Queda pendiente de aprobación por un admin.", "ok")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Ya existe una cuenta con ese email.", "error")
    return render_template("register.html")

# --------- Login/Logout ---------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        pw    = request.form.get("password") or ""
        db = get_db()
        u = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not u:
            flash("Credenciales inválidas.", "error")
            return render_template("login.html")
        cred = db.execute("SELECT salt, pw_hash FROM credentials WHERE user_id=?", (u["id"],)).fetchone()
        if not cred or not verify_password(pw, cred["salt"], cred["pw_hash"]):
            flash("Credenciales inválidas.", "error")
            return render_template("login.html")
        if u["status"] != "APPROVED":
            flash(f"Cuenta con estado {u['status']}. Espera aprobación o contacta con un admin.", "error")
            return render_template("login.html")
        # ok
        session.update({
            "user_id": u["id"],
            "email": u["email"],
            "display_name": u["display_name"],
            "is_admin": bool(u["is_admin"]),
        })
        flash("Sesión iniciada.", "ok")
        return redirect(request.args.get("next") or url_for("profile"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "ok")
    return redirect(url_for("index"))

# --------- Perfil ---------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    me = current_user()
    if request.method == "POST":
        display = (request.form.get("display_name") or "").strip()
        bio     = request.form.get("bio") or ""
        db.execute("UPDATE users SET display_name=?, bio=?, updated_at=? WHERE id=?",
                   (display, bio, datetime.utcnow().isoformat(), me["id"]))
        db.commit()
        session["display_name"] = display
        flash("Perfil actualizado.", "ok")
        return redirect(url_for("profile"))

    # listas seguidores/siguiendo
    following = db.execute("""
        SELECT u.* FROM follows f
        JOIN users u ON u.id=f.followed_id
        WHERE f.follower_id=? AND u.status='APPROVED'
        ORDER BY f.created_at DESC
    """, (me["id"],)).fetchall()
    followers = db.execute("""
        SELECT u.* FROM follows f
        JOIN users u ON u.id=f.follower_id
        WHERE f.followed_id=? AND u.status='APPROVED'
        ORDER BY f.created_at DESC
    """, (me["id"],)).fetchall()

    q = (request.args.get("q") or "").strip().lower()
    results = []
    if q:
        results = db.execute("""
            SELECT * FROM users
            WHERE status='APPROVED' AND id!=? AND (LOWER(email) LIKE ? OR LOWER(display_name) LIKE ?)
            ORDER BY display_name LIMIT 50
        """, (me["id"], f"%{q}%", f"%{q}%")).fetchall()

    return render_template("profile.html", me=me, following=following, followers=followers, results=results, q=q)

@app.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow(user_id):
    me = current_user()
    if me["id"] == user_id:
        flash("No puedes seguirte a ti mismo.", "error")
        return redirect(url_for("profile"))
    db = get_db()
    try:
        db.execute("INSERT INTO follows(follower_id, followed_id, created_at) VALUES(?,?,?)",
                   (me["id"], user_id, datetime.utcnow().isoformat()))
        db.commit()
        flash("Ahora sigues a este usuario.", "ok")
    except sqlite3.IntegrityError:
        # ya seguía → lo tomamos como idempotente
        flash("Ya seguías a este usuario.", "ok")
    return redirect(url_for("profile", q=request.args.get("q","")))

@app.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    me = current_user()
    db = get_db()
    db.execute("DELETE FROM follows WHERE follower_id=? AND followed_id=?", (me["id"], user_id))
    db.commit()
    flash("Has dejado de seguir a este usuario.", "ok")
    return redirect(url_for("profile", q=request.args.get("q","")))

# --------- Admin ---------
@app.route("/admin")
@admin_required
def admin_panel():
    db = get_db()
    pending = db.execute("SELECT * FROM users WHERE status='PENDING' ORDER BY created_at DESC").fetchall()
    users   = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return render_template("admin.html", pending=pending, users=users)

@app.post("/admin/approve/<int:user_id>")
@admin_required
def admin_approve(user_id):
    db = get_db()
    db.execute("UPDATE users SET status='APPROVED', updated_at=? WHERE id=?",
               (datetime.utcnow().isoformat(), user_id))
    db.commit()
    flash("Usuario aprobado.", "ok")
    return redirect(url_for("admin_panel"))

@app.post("/admin/reject/<int:user_id>")
@admin_required
def admin_reject(user_id):
    db = get_db()
    db.execute("UPDATE users SET status='REJECTED', updated_at=? WHERE id=?",
               (datetime.utcnow().isoformat(), user_id))
    db.commit()
    flash("Usuario rechazado.", "ok")
    return redirect(url_for("admin_panel"))

@app.post("/admin/block/<int:user_id>")
@admin_required
def admin_block(user_id):
    db = get_db()
    db.execute("UPDATE users SET status='BLOCKED', updated_at=? WHERE id=?",
               (datetime.utcnow().isoformat(), user_id))
    db.commit()
    flash("Usuario bloqueado.", "ok")
    return redirect(url_for("admin_panel"))

@app.post("/admin/toggle-admin/<int:user_id>")
@admin_required
def admin_toggle_admin(user_id):
    db = get_db()
    u = db.execute("SELECT is_admin FROM users WHERE id=?", (user_id,)).fetchone()
    if u:
        db.execute("UPDATE users SET is_admin=?, updated_at=? WHERE id=?",
                   (0 if u["is_admin"] else 1, datetime.utcnow().isoformat(), user_id))
        db.commit()
        flash("Rol de admin actualizado.", "ok")
    return redirect(url_for("admin_panel"))

@app.post("/admin/delete/<int:user_id>")
@admin_required
def admin_delete(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    flash("Usuario borrado.", "ok")
    return redirect(url_for("admin_panel"))

# ---------------------- MAIN ------------------------
if __name__ == "__main__":
    # para ejecutar directo con: python app.py
    app.run(debug=True)
