from flask import Flask, render_template, jsonify, request, session
from datetime import datetime, timedelta, timezone
import requests
import json

from flask import request, make_response
from flask import redirect, url_for
#from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

from database import User, db
from auth import register, login
from api_manager import update_data
app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SECRET_KEY'] = 'ClaveSecreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/javi/ISI/WiseBet/WiseBet/Sprint3_aplicacion/usuarios.db'  # La ruta a la base de datos SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)

"""
db = SQLAlchemy(app)

# Definición del modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(80))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(15)) """

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

        # Lógica para obtener y filtrar apuestas con valor
        eventos_con_valor = []  # Aquí se almacenarán las apuestas filtradas
        url = f'https://api.the-odds-api.com/v4/sports/soccer_spain_la_liga/odds'
        
        params = {
            'api_key': API_KEY,
            'regions': 'us',
            'markets': 'h2h',
            'oddsFormat': 'decimal',
            'dateFormat': 'iso',
        }
        
        response = requests.get(url, params=params)

        if response.status_code == 200:
            eventos = response.json()
            print('Remaining requests', response.headers['x-requests-remaining'])
            print('Used requests', response.headers['x-requests-used'])
            print("Eventos recibidos:", len(eventos))  # Ver cuántos eventos recibimos
            for evento in eventos:
                for bookmaker in evento['bookmakers']:
                    for market in bookmaker['markets']:
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                # Implementación del cálculo del valor esperado
                                probabilidad_estimada = estimar_probabilidad_de_victoria(outcome['name'])
                                cuota = outcome['price']
                                valor_esperado = (probabilidad_estimada * cuota) - 1
                                
                                if valor_esperado > 1.5:
                                    eventos_con_valor.append({
                                        'partido': f"{evento['home_team']} vs {evento['away_team']}",
                                        'cuota': cuota,
                                        'equipo': outcome['name'],
                                        'casa': bookmaker['title']
                                        
                                        #'valor_esperado': valor_esperado
                                    })
                                    #print(f"Añadido evento con valor: {outcome['name']} con cuota {cuota}")
        else:
            print(f"Error al obtener las cuotas: {response.status_code}")
        

        return render_template('dashboard.html', email=email, standings=standings, dataFixtures=dataFixtures, eventos_con_valor=eventos_con_valor)

    except (IOError, ValueError):
        return 'Error al cargar los datos desde el archivo', 500

    


    ########OBTENCION DE CUOTAS

def estimar_probabilidad_de_victoria(equipo):
    # Este es un ejemplo simplificado. Tu lógica/modelo debe ir aquí
    probabilidades = {
        "Real Madrid": 0.75,
        "Barcelona": 0.7,
        "Atlético de Madrid": 0.65,
        "Sevilla": 0.6,
        "Valencia": 0.55,
        # Añade más equipos y sus probabilidades estimadas de ganar
    }
    return probabilidades.get(equipo, 0.5)  # Devuelve 0.5 como probabilidad por defecto si el equipo no está en el diccionario

def load_api_key_cuo():
    with open('configCuo.json', 'r') as config_file:
        config = json.load(config_file)
    return config.get('api_key', None)

API_KEY = load_api_key_cuo()
SPORT='soccer_spain_la_liga'


if __name__ == '__main__':
    #db.create_all()
    app.run(debug=True)
