from api_manager import load_api_key_cuo
import requests

API_KEY = load_api_key_cuo()
SPORT='soccer_spain_la_liga'

def calcular_valor_esperado(probabilidad_estimada, cuota):
    """
    Calcula el valor esperado de una apuesta dados la probabilidad estimada y la cuota.
    """
    valor_esperado = (probabilidad_estimada * cuota) - 1
    return valor_esperado

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


def filtrar_apuestas_con_valor(eventos):
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
        #print("Eventos recibidos:", len(eventos))  # Ver cuántos eventos recibimos
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

    return eventos_con_valor
