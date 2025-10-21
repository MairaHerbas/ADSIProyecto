# app.py

from flask import Flask, render_template

# Configuración de carpetas que DEBE estar correcta ahora:
app = Flask(__name__,
            template_folder='html',
            static_folder='static')

@app.route('/')
def index():
    # Renderiza la plantilla correcta, que está en la subcarpeta 'bienvenido'
    return render_template('bienvenido/index.html')

@app.route('/registro')
def registro():
    # Asume que tienes un archivo registro.html
    return render_template('bienvenido/registro.html')

@app.route('/iniciar_sesion')
def iniciar_sesion():
    # Asume que tienes un archivo iniciarSesion.html
    return render_template('bienvenido/iniciarSesion.html')

def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("home"))
        if session.get("role") != "admin":
            flash("No tienes permisos para acceder a Admin.", "danger")
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapper

def get_current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])

# --- HOME = Bienvenida + Login ---
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Credenciales incorrectas.", "danger")
            return render_template("welcome_login.html")

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["role"] = user.role
        flash(f"¡Bienvenido/a, {user.name}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("welcome_login.html")

# --- REGISTRO ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not name or not email or not password or not confirm:
            flash("Rellena todos los campos.", "warning")
            return render_template("register.html")
        if password != confirm:
            flash("Las contraseñas no coinciden.", "warning")
            return render_template("register.html")
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "warning")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("Ya existe una cuenta con ese email.", "warning")
            return render_template("register.html")

        new_user = User(name=name, email=email, role="user")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("home"))

    return render_template("register.html")

# --- PANEL (DESPUÉS DE LOGIN) ---
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard.html", name=session.get("user_name"), role=session.get("role"))

# --- LOGOUT ---
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("home"))

# --- ADMIN: LISTADO Y PROMOCIÓN/DEGRADACIÓN ---
@app.route("/admin")
@admin_required
def admin():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin.html", users=users, me_id=session["user_id"])

@app.post("/admin/promote/<int:user_id>")
@admin_required
def promote_user(user_id):
    me_id = session["user_id"]
    if user_id == me_id:
        flash("No puedes cambiar tu propio rol desde aquí.", "warning")
        return redirect(url_for("admin"))
    u = User.query.get_or_404(user_id)
    u.role = "admin"
    db.session.commit()
    flash(f"{u.name} ahora es administrador.", "success")
    return redirect(url_for("admin"))

@app.post("/admin/demote/<int:user_id>")
@admin_required
def demote_user(user_id):
    me_id = session["user_id"]
    if user_id == me_id:
        flash("No puedes degradarte a ti mismo desde aquí.", "warning")
        return redirect(url_for("admin"))
    u = User.query.get_or_404(user_id)
    u.role = "user"
    db.session.commit()
    flash(f"{u.name} vuelve a ser usuario.", "info")
    return redirect(url_for("admin"))

# --- CLI: crear un admin “a mano” ---
@app.cli.command("create-admin")
def create_admin():
    """Crea un admin rápido: flask --app app.py create-admin"""
    email = "admin@demo.com"
    name = "Admin"
    password = "admin123"
    if User.query.filter_by(email=email).first():
        print("Ya existe:", email)
        return
    u = User(name=name, email=email, role="admin")
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    print(f"Admin creado: {email} / {password} (cámbialo luego)")

if __name__ == "__main__":
    app.run(debug=True)
