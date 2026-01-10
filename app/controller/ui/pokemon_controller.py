from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.database.connection import db
from app.controller.model.pokemon_model import Equipo, Pokemon
from app.utils import login_required

pokemon_bp = Blueprint('pokemon', __name__)


# --- BÚSQUEDA POKEDEX ---
@pokemon_bp.route('/pokedex')
@login_required
def pokedex_buscador():
    q = request.args.get('q', '')
    t = request.args.get('tipo', '')
    g = request.args.get('gen', '')

    query = Pokemon.query
    if q: query = query.filter(Pokemon.nombre.ilike(f'%{q}%'))
    if t: query = query.filter(Pokemon.tipos.ilike(f'%{t}%'))
    if g: query = query.filter_by(generacion=g)

    pokemons = query.limit(100).all()
    return render_template('miguel-adrian/index.html', pokemons=pokemons, q=q, tipo_sel=t, gen_sel=g)


@pokemon_bp.route('/pokedex/<int:id>')
@login_required
def pokedex_detalle(id):
    poke = Pokemon.query.get_or_404(id)
    return render_template('miguel-adrian/index.html', poke=poke)


from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from app.database.connection import db
from app.controller.model.pokemon_model import Equipo, Pokemon, PokemonEquipo
from app.controller.model.user_model import Event  # Importamos Evento para el Changelog
from app.utils import login_required

pokemon_bp = Blueprint('pokemon', __name__)


# --- CONSULTAR EQUIPO (Diagrama 2) ---
@pokemon_bp.route('/equipos')
@login_required
def consultar_equipos():
    # Nodo 4.1: SELECT * FROM Equipo WHERE user_id...
    mis_equipos = Equipo.query.filter_by(user_id=session['user_id']).order_by(Equipo.created_at.desc()).all()
    # La vista se encargará de iterar los pokemons (Nodo 3.2 del diagrama)
    return render_template('equipo/consultarEquipo.html', equipos=mis_equipos)


# --- CREAR EQUIPO (Diagrama 1) ---
@pokemon_bp.post('/equipos/crear')
@login_required
def crear_equipo():
    nombre = request.form.get('nombre_equipo')
    if not nombre:
        flash("El nombre es obligatorio", "warning")
        return redirect(url_for('pokemon.consultar_equipos'))

    # 1. Nodo 3.1.1: INSERT INTO Equipo
    nuevo_equipo = Equipo(nombre_equipo=nombre, user_id=session['user_id'])
    db.session.add(nuevo_equipo)
    db.session.flush()  # Hacemos flush para obtener el ID antes del commit (Nodo 3.1.4)

    # 2. Nodo 3.1.5: registrarEvento (Changelog)
    nuevo_evento = Event(
        user_id=session['user_id'],
        event_type="CREACION_EQUIPO",
        description=f"Ha creado el equipo '{nombre}'"
    )
    db.session.add(nuevo_evento)

    db.session.commit()
    flash("Equipo creado correctamente", "success")
    return redirect(url_for('pokemon.consultar_equipos'))


# --- EDITAR EQUIPO (Diagrama 3) ---
@pokemon_bp.route('/equipos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_equipo(id):
    equipo = Equipo.query.get_or_404(id)

    # Seguridad
    if equipo.user_id != session['user_id']:
        return redirect(url_for('pokemon.consultar_equipos'))

    if request.method == 'POST':
        # Nodo 5.1.1: UPDATE Equipo SET nombre...
        nuevo_nombre = request.form.get('nombre_equipo')
        if nuevo_nombre:
            equipo.nombre_equipo = nuevo_nombre

        # Nodo 5.1.2: DELETE FROM Pokemon_Equipo WHERE equipo_id...
        # Eliminamos los pokemons antiguos para insertar los nuevos limpios
        PokemonEquipo.query.filter_by(equipo_id=equipo.id).delete()

        # Nodo 5.1.3: INSERT INTO pokemon_equipo (Loop para cada pokemon)
        # Asumimos que el formulario envía listas de IDs de pokemon, apodos, etc.
        pokemon_ids = request.form.getlist('pokemon_id')
        apodos = request.form.getlist('apodo')
        # ... recoge habilidades y movimientos igual ...

        for index, pid in enumerate(pokemon_ids):
            if pid:  # Si hay ID
                nuevo_pk_eq = PokemonEquipo(
                    equipo_id=equipo.id,
                    pokemon_id=int(pid),
                    orden=index + 1,
                    apodo=apodos[index] if index < len(apodos) else None,
                    # habilidad=..., movimiento=... (Recoger del form)
                    fecha_captura=datetime.utcnow()
                )
                db.session.add(nuevo_pk_eq)

        # Registrar Evento de Edición (Requisito implícito del Changelog)
        evento_edit = Event(
            user_id=session['user_id'],
            event_type="EDICION_EQUIPO",
            description=f"Ha editado el equipo '{equipo.nombre_equipo}'"
        )
        db.session.add(evento_edit)

        db.session.commit()
        flash("Equipo actualizado", "success")
        return redirect(url_for('pokemon.consultar_equipos'))

    # GET: Mostrar formulario de edición
    return render_template('equipo/editarEquipo.html', equipo=equipo)


@pokemon_bp.post('/equipos/eliminar/<int:id>')
@login_required
def eliminar_equipo(id):
    equipo = Equipo.query.get_or_404(id)
    if equipo.user_id == session['user_id']:
        nombre_bak = equipo.nombre_equipo
        db.session.delete(equipo)

        # Registrar evento de borrado
        evento_del = Event(
            user_id=session['user_id'],
            event_type="ELIMINACION_EQUIPO",
            description=f"Ha eliminado el equipo '{nombre_bak}'"
        )
        db.session.add(evento_del)

        db.session.commit()
        flash("Equipo eliminado", "success")
    return redirect(url_for('pokemon.consultar_equipos'))