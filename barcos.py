import websocket
import json

# 1. Saca tu API key gratis en aisstream.io (te la dan en 2 min)
API_KEY = "c9448c359fff4a189388f41f642c38861b9a73c5"

def on_message(ws, message):
    datos = json.loads(message)
    # Esto ya es un barco REAL moviéndose ahora mismo
    barco = datos['MetaData']
    print(f"Barco: {barco['ShipName']} | Lat: {datos['Message']['PositionReport']['Latitude']} | Lon: {datos['Message']['PositionReport']['Longitude']}")
    
    # Aquí lo guardas en tu json como hacías
    with open("posiciones.json", "w") as archivo:
        json.dump(barco, archivo, indent=4)

def on_open(ws):
    # Le dices: "Quiero ver todos los barcos del Atlántico"
    subscribe = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[-90, -180], [90, 180]]], # todo el mundo
        "FilterMessageTypes": ["PositionReport"]
    }
    ws.send(json.dumps(subscribe))

ws = websocket.WebSocketApp("wss://stream.aisstream.io/v0/stream", on_message=on_message, on_open=on_open)
ws.run_forever()
