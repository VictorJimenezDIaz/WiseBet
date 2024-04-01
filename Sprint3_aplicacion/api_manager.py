import requests
import json
from datetime import datetime, timedelta, timezone
import pytz


def load_api_key():
    with open('configEst.json', 'r') as config_file:
        config = json.load(config_file)
    return config.get('api_key', None)

def load_api_key_cuo():
    with open('configCuo.json', 'r') as config_file:
        config = json.load(config_file)
    return config.get('api_key', None)


def convertir_a_hora_local(fecha_utc_str, zona_horaria_deseada='Europe/Madrid'):
    # Intenta parsear la fecha/hora con zona horaria; si falla, intenta sin la zona horaria
    try:
        fecha_utc = datetime.strptime(fecha_utc_str, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        # Parsear sin zona horaria y asumir UTC
        fecha_utc = datetime.strptime(fecha_utc_str, '%Y-%m-%d %H:%M:%S')
        fecha_utc = fecha_utc.replace(tzinfo=pytz.utc)
    
    zona_horaria = pytz.timezone(zona_horaria_deseada)
    fecha_local = fecha_utc.astimezone(zona_horaria)
    return fecha_local 


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

    fecha_hoy = datetime.now(pytz.timezone('Europe/Madrid'))
    jornadas_futuras = set()
    partidos_por_jornada = {}

    for partido in dataFixtures['response']:
        fecha_partido = convertir_a_hora_local(partido['fixture']['date'])
        partido['fixture']['date'] = fecha_partido.strftime('%Y-%m-%d %H:%M:%S')

        print(fecha_partido)
        jornada = partido['league']['round']
        if fecha_partido >= fecha_hoy:
            partidos_por_jornada.setdefault(jornada, []).append(partido)

    jornada_proxima = max(partidos_por_jornada.keys(), key=lambda j: len(partidos_por_jornada[j]))
    for jornada in jornadas_futuras:
        partidos = partidos_por_jornada[jornada]
        partidos_finalizados = sum(1 for p in partidos if p['fixture']['status']['short'] == 'FT')

        if partidos_finalizados >= 10:  # Asumiendo que una jornada completa tiene 10 partidos
            fecha_ultimo_partido = max(p['fixture']['date'] for p in partidos)
            fecha_ultimo_partido = datetime.strptime(fecha_ultimo_partido, '%Y-%m-%dT%H:%M:%S%z')
            if fecha_hoy - fecha_ultimo_partido > timedelta(days=1):
                jornada_proxima = jornada
                break

    if not jornada_proxima:
        jornada_proxima = min(jornadas_futuras, key=lambda x: min(datetime.strptime(p['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z') for p in partidos_por_jornada[x]))

    proximos_partidos = partidos_por_jornada.get(jornada_proxima, [])
    proximos_partidos_ordenados = sorted(proximos_partidos, key=lambda p: convertir_a_hora_local(p['fixture']['date']))
    #print(proximos_partidos_ordenados)

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