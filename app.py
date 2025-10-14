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

if __name__ == '__main__':
    app.run(debug=True)