from flask import Flask, jsonify, render_template
from datetime import datetime, timedelta, timezone
import requests
import json
import pytz

app = Flask(__name__)

@app.template_filter('to_datetime')
def to_datetime_filter(value, format='%Y-%m-%dT%H:%M:%S%z'):
    return datetime.strptime(value, format).strftime('%d/%m/%Y %H:%M')


def load_api_key():
    with open('configEst.json', 'r') as config_file:
        config = json.load(config_file)
        return config.get('api_key', None)

@app.route('/api/standings')
def get_standings():
    url = "https://api-football-v1.p.rapidapi.com/v3/standings"
    querystring = {"season": "2023", "league": "140"}

    # Obtener la clave de API desde el archivo de configuración
    api_key = load_api_key()

    if api_key is None:
        return "Error: Clave de API no encontrada en el archivo de configuración."

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    # Imprimir los datos en la consola para comprender su estructura
    #print(data)

    return render_template('standings.html', data=data)


@app.route('/')
def get_partidosJornada():
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
    dataFixtures = responseFixtures.json()

    #print(dataFixtures)
    """ 
    fechaHoy = datetime.now(timezone.utc)
    print(fechaHoy)  # Debería mostrar la fecha y hora actuales en formato UTC
    print(len(dataFixtures['response']))  # Debería mostrar el número de partidos disponibles

    proximos_partidos = [partido for partido in dataFixtures['response']
                     if datetime.strptime(partido['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z') > fechaHoy]
    """
    
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

    # Si no se encuentra jornada próxima bajo estos criterios, se elige la más cercana por fecha
    if not jornada_proxima:
        jornada_proxima = min(jornadas_futuras, key=lambda x: min(datetime.strptime(p['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z') for p in partidos_por_jornada[x]))

    proximos_partidos = partidos_por_jornada.get(jornada_proxima, [])
    proximos_partidos_ordenados = sorted(proximos_partidos, key=lambda p: datetime.strptime(p['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z'))

    return render_template('landing.html',dataFixtures=proximos_partidos_ordenados)





if __name__ == '__main__':
    app.run(debug=True)
