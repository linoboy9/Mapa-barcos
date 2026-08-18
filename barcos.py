import websocket
import json
import threading
import os
import time
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

import os

API_KEY = os.environ.get("AIS_API_KEY")

barcosguardados = {}

def on_message(ws, message):
    try:
        datos = json.loads(message)
        if 'MetaData' in datos:
            barco = datos['MetaData']
            mmsi = barco.get('MMSI')
            if mmsi:
                barcos_guardados[mmsi] = barco
                if len(barcos_guardados) > 50:
                    viejo_mmsi = list(barcos_guardados.keys())[0]
                    del barcos_guardados[viejo_mmsi]
                print(f"🚢 Barco: {barco.get('ShipName', 'Desconocido')} | Lat: {barco.get('latitude')} | Lon: {barco.get('longitude')}")
    except Exception as e:
        print(f"Error: {e}")

def on_open(ws):
    print("✅ ¡Conectado con éxito a aisstream.io!")
    subscribe = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[-90, -180], [90, 180]]]
    }
    ws.send(json.dumps(subscribe))

def on_error(ws, error):
    print(f"❌ Error WS: {error}")

def on_close(ws, code, msg):
    print("🔒 WebSocket cerrado temporalmente.")

def iniciar_tracker():
    # Esperamos 10 segundos al arrancar para dejar respirar a la API si hubo bloqueo 429
    time.sleep(10)
    while True:
        try:
            print("🔄 Conectando al stream de barcos...")
            ws = websocket.WebSocketApp(
                "wss://stream.aisstream.io/v0/stream",
                on_message=on_message,
                on_open=on_open,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"Error en tracker: {e}")
        
        # Esperamos 15 segundos antes de reintentar si se cae, evitando el error 429
        time.sleep(15)

hilo = threading.Thread(target=iniciar_tracker, daemon=True)
hilo.start()

@app.route('/')
def home():
    return "API de Barcos Activa"

@app.route('/datos')
def ver_datos():
    return jsonify(list(barcosguardados.values()))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
