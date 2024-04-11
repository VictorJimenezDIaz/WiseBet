from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from datetime import datetime, timedelta, timezone
import requests
import json
import uuid
import os

from database import User, db
from auth import register, login
from api_manager import update_data
from apuestas import calcular_valor_esperado, filtrar_apuestas_con_valor, estimar_probabilidad_de_victoria

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'usuarios.db')

# Configuración de la base de datos SQLite
app.config['SECRET_KEY'] = 'ClaveSecreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)


# Ruta para el registro de usuarios
@app.route("/register", methods=['POST'])
def handler_register():
    if request.method == 'POST':
        # Llama a la función register() de auth.py con los datos del formulario
        response = register(request.json)
        return response
    else:
        # Maneja cualquier otro método que no sea POST
        return "Method Not Allowed", 405  # Código de estado HTTP 405 para método no permitido


@app.route('/login', methods=['POST'])
def handler_login():
    if request.method == 'POST':
        # Llama a la función login() de auth.py con los datos del formulario
        response = login(request.json)
        return response
    else:
        # Maneja cualquier otro método que no sea POST
        return "Method Not Allowed", 405  # Código de estado HTTP 405 para método no permitido



@app.template_filter('to_datetime')
def to_datetime_filter(value, format='%Y-%m-%dT%H:%M:%S%z'):
    return datetime.strptime(value, format).strftime('%d/%m/%Y %H:%M')


@app.route('/update-data')
def handler_update_data():
    message = update_data()
    return jsonify({"message": message})

@app.route('/')
def home():
    try:
        with open('data.json', 'r') as f:
            #dataFixtures = json.load(f)
            data = json.load(f)
        return render_template('landing.html', dataFixtures=data['fixtures'], standings=data['standings'])
    except (IOError, ValueError):
        return 'Error al cargar los datos desde el archivo', 500
    
@app.route('/quienes-somos')
def quienes_somos():
    return render_template('about.html')

@app.route('/precios')
def precios():
    return render_template('pricing.html')

@app.route('/apis')
def apis():
    return render_template('api_info.html')
    
@app.route('/iniciar-sesion')
def iniciar_sesion():
    return render_template('login.html')

@app.route('/cerrar-sesion')
def cerrar_sesion():
    # Elimina el usuario de la sesión
    session.pop('user_id', None)
    return redirect(url_for('home'))  # Redirige a la página de inicio

@app.route('/apostar')
def apostar():
    return render_template('apostar.html')

@app.route('/historico')
def historico():
    if 'user_id' not in session:
        return redirect('/iniciar-sesion')

    # Obtiene el ID del usuario de la sesión
    user_id = session['user_id']
    
    # Busca al usuario en la base de datos por su ID
    user = User.query.get(user_id)

    if user and user.email:
        email = user.email
    else:
        email = "Correo no encontrado"
    
    # Pasa el email del usuario a la plantilla
    return render_template('historico.html', email=email)

@app.route('/dashboard')
def dashboard():
    try:
        # Verifica si hay una sesión activa
        if 'user_id' not in session:
            return redirect('/iniciar-sesion')

        # Obtén el ID del usuario de la sesión
        user_id = session['user_id']
        
        # Busca al usuario en la base de datos por su ID
        user = User.query.get(user_id)

        if user and user.email:
            email = user.email
        else:
            email = "Correo no encontrado"

        with open('data.json', 'r') as f:
            data = json.load(f)
        standings = data.get('standings', [])
        dataFixtures = data.get('fixtures', [])

        eventos = dataFixtures
        eventos_con_valor = filtrar_apuestas_con_valor(eventos)

        if user.subscription == 'gratis':
            eventos_con_valor = eventos_con_valor[:int(len(eventos_con_valor) * 0.30)]
        elif user.subscription == 'premium':
            eventos_con_valor = eventos_con_valor[:int(len(eventos_con_valor) * 0.50)]
        
        return render_template('dashboard.html', email=email, standings=standings, dataFixtures=dataFixtures, eventos_con_valor=eventos_con_valor)

    except (IOError, ValueError):
        return 'Error al cargar los datos desde el archivo', 500
    
    


if __name__ == '__main__':
    #db.create_all()
    app.run(debug=True)
