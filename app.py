# app.py

from flask import Flask, render_template, request

from pokedex.cargadatosPokedex import PokemonModel

# 1. Configuración única de la APP
app = Flask(__name__,
            template_folder='html',
            static_folder='static')

# 2. Configuración de la Base de Datos (Se ejecuta una sola vez al inicio)
modelo = PokemonModel()
modelo.inicializar_db()

# Si la base de datos está vacía, descarga los datos (esto puede tardar un poco la primera vez)
if modelo.db_esta_vacia():
    print("Base de datos vacía. Descargando datos...")
    modelo.descargar_datos(386)


# --- RUTA PRINCIPAL (FUSIONADA) ---
@app.route('/')
def index():
    # Esta función maneja TANTO la vista de bienvenida COMO la búsqueda

    # 1. Recoge filtros del formulario (si el usuario buscó algo)
    q = request.args.get('q', '')
    t = request.args.get('tipo', '')
    g = request.args.get('gen', '')

    # 2. Busca los pokemons
    pokemons = modelo.buscar_pokemons(nombre=q, tipo=t, generacion=g)

    # 3. Renderiza la plantilla 'bienvenido/index.html' enviándole los datos
    return render_template('bienvenido/index.html',
                           pokemons=pokemons,
                           q=q,
                           tipo_sel=t,
                           gen_sel=g)


@app.route('/registro')
def registro():
    return render_template('bienvenido/registro.html')


@app.route('/iniciar_sesion')
def iniciar_sesion():
    return render_template('bienvenido/iniciarSesion.html')


#

@app.route('/pokemon/<int:id_poke>')
def detalle(id_poke):
    poke = modelo.obtener_por_id(id_poke)
    if poke:
        return render_template('bienvenido/detalle.html', poke=poke)
    else:
        return "Pokemon no encontrado", 404


if __name__ == '__main__':
    app.run(debug=True)