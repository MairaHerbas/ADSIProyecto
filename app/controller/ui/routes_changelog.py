from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from app.controller.model.user_model import User
from app.controller.sistema_pokedex import SistemaPokedex

changelog_bp = Blueprint('changelog', __name__)

# RUTA 1: Carga la página HTML (La vista principal)
@changelog_bp.route('/notificaciones')
def ver_notificaciones():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Renderizamos la plantilla vacía, el JS se encargará de pedir los datos después
    return render_template('index.html') 
    # NOTA: O si tienes un html específico 'changelog.html', usa ese. 
    # El JS buscará donde inyectar la lista.


# RUTA 2: API JSON (Esta es la que llama el archivo notifications.js)
@changelog_bp.route('/api/notifications')
def api_notifications():
    if 'user_id' not in session:
        return jsonify([]) # Retornar lista vacía si no hay sesión

    user_id = session['user_id']
    current_user = User.get_by_id(user_id)

    # 1. Obtenemos los objetos del dominio (Clase ChangelogEvent)
    eventos_sistema = SistemaPokedex.cargarNotificaciones(current_user)

    # 2. Convertimos al formato JSON exacto que pide notifications.js
    datos_para_el_frontend = []

    for evento in eventos_sistema:
        # A) TRADUCIR ID USUARIO A NOMBRE
        # El JS espera un nombre, no un número. Buscamos el usuario.
        usuario_obj = User.get_by_id(evento.id_usuario)
        nombre_usuario = usuario_obj.username if usuario_obj else "Desconocido"

        # B) SEPARAR FECHA Y HORA
        # La DB devuelve "YYYY-MM-DD HH:MM:SS"
        # El JS necesita date: "YYYY-MM-DD" y time: "HH:MM:SS" por separado
        partes_fecha = str(evento.fecha).split(' ')
        fecha_str = partes_fecha[0]
        hora_str = partes_fecha[1] if len(partes_fecha) > 1 else "00:00"

        # C) CREAR EL DICCIONARIO CON LAS CLAVES EXACTAS DEL JS
        datos_para_el_frontend.append({
            "user": nombre_usuario,      # JS espera 'user'
            "type": evento.tipo,         # JS espera 'type' (coincide valor, cambiamos clave)
            "desc": evento.descripcion,  # JS espera 'desc', nosotros tenemos 'descripcion'
            "date": fecha_str,           # JS espera 'date'
            "time": hora_str             # JS espera 'time'
        })

    # Devolvemos la lista en formato JSON
    return jsonify(datos_para_el_frontend)