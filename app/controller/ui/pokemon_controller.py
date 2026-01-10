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
    return render_template('bienvenido/index.html', pokemons=pokemons, q=q, tipo_sel=t, gen_sel=g)


@pokemon_bp.route('/pokedex/<int:id>')
@login_required
def pokedex_detalle(id):
    poke = Pokemon.query.get_or_404(id)
    return render_template('bienvenido/detalle.html', poke=poke)


# --- CRUD EQUIPOS ---
@pokemon_bp.route('/equipos')
@login_required
def consultar_equipos():
    mis_equipos = Equipo.query.filter_by(user_id=session['user_id']).all()
    return render_template('equipo/consultarEquipo.html', equipos=mis_equipos)


@pokemon_bp.post('/equipos/crear')
@login_required
def crear_equipo():
    nombre = request.form.get('nombre_equipo')
    if nombre:
        nuevo = Equipo(nombre_equipo=nombre, user_id=session['user_id'])
        db.session.add(nuevo)
        db.session.commit()
        flash("Equipo creado", "success")
    return redirect(url_for('pokemon.consultar_equipos'))


@pokemon_bp.post('/equipos/eliminar/<int:id>')
@login_required
def eliminar_equipo(id):
    equipo = Equipo.query.get_or_404(id)
    if equipo.user_id == session['user_id']:
        db.session.delete(equipo)
        db.session.commit()
        flash("Equipo eliminado", "success")
    return redirect(url_for('pokemon.consultar_equipos'))