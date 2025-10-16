from flask import Flask, render_template
app = Flask(__name__,
            template_folder='html',
            static_folder='static')
@app.route('/')
def index():
    # Renderiza la plantilla correcta, que está en la subcarpeta 'bienvenido'
    return render_template('bienvenido/index.html')

@app.route('/registro')
def registro():
    return render_template('bienvenido/registro.html')

@app.route('/iniciar_sesion')
def iniciar_sesion():
    return render_template('equipo/iniciarSesion.html')

@app.route('/consultar_equipo')
def consultar_equipo():
    return render_template('equipo/consultarEquipo.html')

@app.route('/editar_equipo')
def editar_equipo():
    return render_template('equipo/editarEquipo.html')

if __name__ == '__main__':
    app.run(debug=True)