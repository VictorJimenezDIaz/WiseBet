from flask import Flask, render_template, jsonify, request
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
#app.config['SECRET_KEY'] = 'ItsIsNotAgoodIdeaToPutYourSecretKEYhere'
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
    app.logger.debug("Usuario registrado correctamente. Redirigiendo a /dashboard.")
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

@app.route('/dashboard')
def dashboard():
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        standings = data.get('standings', [])  # Obtener la lista de clasificaciones
        return render_template('dashboard.html', standings=standings)
    except (IOError, ValueError):
        return 'Error al cargar los datos desde el archivo', 500

if __name__ == '__main__':
    #db.create_all()
    app.run(debug=True)
