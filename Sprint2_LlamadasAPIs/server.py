from flask import Flask, jsonify, render_template
import requests
import json

app = Flask(__name__)

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


if __name__ == '__main__':
    app.run(debug=True)
