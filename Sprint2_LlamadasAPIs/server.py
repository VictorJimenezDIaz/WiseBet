from flask import Flask, render_template, jsonify, request, session
from datetime import datetime, timedelta, timezone
import requests
import json

from flask import request, make_response
from flask import redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SECRET_KEY'] = 'ClaveSecreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/javi/ISI/WiseBet/WiseBet/Sprint2_LlamadasAPIs/usuarios.db'  # La ruta a la base de datos SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

# Definición del modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(80))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(15))

# Ruta para el registro de usuarios
@app.route("/register", methods=['POST'])
def register():
    
    # Verifica si todos los campos necesarios están presentes
    if request.headers.get('Content-Type') == 'application/json':
        # Obtener los datos JSON del formulario
        data = request.get_json()
        print("Data received:", data)  # Imprime los datos recibidos desde el cliente
    else:
        # Si la solicitud no es JSON, devolver un error
        print("Invalid Content-Type:", request.headers.get('Content-Type'))  # Imprime el tipo de contenido de la solicitud
        return jsonify({"error": "Invalid Content-Type"}), 400
    
    # Verifica si todos los campos necesarios están presentes
    if "nombre" not in data or "apellidos" not in data or "correo" not in data or "telefono" not in data or "password" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    # Comprueba si el usuario ya existe en la base de datos
    if User.query.filter_by(email=data["correo"]).first():
        return jsonify({"error": "Email already exists"}), 400

    # Crea un nuevo usuario
    new_user = User(
        username=data["nombre"],  # Se utiliza 'nombre' como username
        password=generate_password_hash(data["password"]),
        email=data["correo"],
        phone=data["telefono"]
    )

    # Agrega el nuevo usuario a la base de datos
    db.session.add(new_user)
    db.session.commit()

    #return jsonify({"message": "User registered successfully"}), 201
    # Después de que el usuario se haya registrado correctamente
    session['user_id'] = new_user.id  # Almacena el ID del usuario recién creado en la sesión

    app.logger.debug("Usuario registrado correctamente. Redirigiendo a /dashboard.")
    return redirect("/dashboard")


@app.route('/login', methods=['POST'])
def login():
    # Verifica si todos los campos necesarios están presentes
    if request.headers.get('Content-Type') == 'application/json':
        data = request.get_json()
    else:
        return jsonify({"error": "Invalid Content-Type"}), 400

    email = data.get('correo')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Si la validación es correcta, puedes iniciar sesión al usuario.
    session['user_id'] = user.id  # Por ejemplo, almacenando el ID del usuario en la sesión.
    app.logger.debug("Usuario logueado correctamente. Redirigiendo a /dashboard.")
    return redirect("/dashboard")



@app.template_filter('to_datetime')
def to_datetime_filter(value, format='%Y-%m-%dT%H:%M:%S%z'):
    return datetime.strptime(value, format).strftime('%d/%m/%Y %H:%M')

def load_api_key():
    with open('configEst.json', 'r') as config_file:
        config = json.load(config_file)
    return config.get('api_key', None)

@app.route('/update-data')
def update_data():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"season": "2023", "league": "140"}
    api_key = load_api_key()

    if api_key is None:
        return "Error: Clave de API no encontrada en el archivo de configuración."

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    responseFixtures = requests.get(url, headers=headers, params=querystring)

    if responseFixtures.status_code != 200:
        # Si la respuesta de la API no es exitosa, regresa un mensaje de error.
        return f'Error al obtener los datos de la API: {responseFixtures.status_code}'

    dataFixtures = responseFixtures.json()

    fecha_hoy = datetime.now(timezone.utc)
    jornadas_futuras = set()
    partidos_por_jornada = {}

    for partido in dataFixtures['response']:
        fecha_partido = datetime.strptime(partido['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z')
        jornada = partido['league']['round']
        if fecha_partido >= fecha_hoy:
            jornadas_futuras.add(jornada)
            partidos_por_jornada.setdefault(jornada, []).append(partido)

    jornada_proxima = None
    for jornada in jornadas_futuras:
        partidos = partidos_por_jornada[jornada]
        partidos_finalizados = sum(1 for p in partidos if p['fixture']['status']['short'] == 'FT')

        if partidos_finalizados >= 8:  # Asumiendo que una jornada completa tiene 10 partidos
            fecha_ultimo_partido = max(p['fixture']['date'] for p in partidos)
            fecha_ultimo_partido = datetime.strptime(fecha_ultimo_partido, '%Y-%m-%dT%H:%M:%S%z')
            if fecha_hoy - fecha_ultimo_partido > timedelta(days=1):
                jornada_proxima = jornada
                break

    if not jornada_proxima:
        jornada_proxima = min(jornadas_futuras, key=lambda x: min(datetime.strptime(p['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z') for p in partidos_por_jornada[x]))

    proximos_partidos = partidos_por_jornada.get(jornada_proxima, [])
    proximos_partidos_ordenados = sorted(proximos_partidos, key=lambda p: datetime.strptime(p['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z'))

    url_standings = "https://api-football-v1.p.rapidapi.com/v3/standings"
    querystring_standings = {"season": "2023", "league": "140"}
    response_standings = requests.get(url_standings, headers=headers, params=querystring_standings)

    if response_standings.status_code != 200:
        return f'Error al obtener los datos de la clasificación de la API: {response_standings.status_code}'

    data_standings = response_standings.json()
    
    data = {
        'fixtures': proximos_partidos_ordenados,  # Asume que ya has definido esta variable
        'standings': data_standings['response']
    }
    
    # Guardar los próximos partidos ordenados en un archivo JSON.
    with open('data.json', 'w') as f:
        json.dump(data, f)

    return 'Datos actualizados y guardados en data.json'

@app.route('/')
def home():
    try:
        with open('data.json', 'r') as f:
            #dataFixtures = json.load(f)
            data = json.load(f)
        return render_template('landing.html', dataFixtures=data['fixtures'], standings=data['standings'])
    except (IOError, ValueError):
        return 'Error al cargar los datos desde el archivo', 500
    
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

API_KEY = 
SPORT='soccer_spain_la_liga'


if __name__ == '__main__':
    #db.create_all()
    app.run(debug=True)
