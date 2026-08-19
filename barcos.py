import websocket
import json
import threading
import os
import time
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("AIS_API_KEY")

barcosguardados = {}
lock = threading.Lock()

def on_message(ws, message):
    try:
        datos = json.loads(message)
        if 'MetaData' in datos:
            meta = datos['MetaData']
            mmsi = meta.get('MMSI')
            nombre = meta.get('ShipName', 'Desconocido').strip()
            lat = meta.get('latitude')
            lon = meta.get('longitude')
            
            if mmsi and lat is not None and lon is not None:
                with lock:
                    barcosguardados[mmsi] = meta
                    print(f"🚢 Barco: {nombre} | Lat: {lat} | Lon: {lon}", flush=True)
                    if len(barcosguardados) > 300:
                        viejo_mmsi = list(barcosguardados.keys())[0]
                        del barcosguardados[viejo_mmsi]
    except Exception as e:
        pass

def on_open(ws):
    print("🟢 Conectado a AISStream. Enviando suscripción...", flush=True)
    payload = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[50.0, 2.0], [54.0, 7.0]]],
        "FilterMessageTypes": ["PositionReport"]
    }
    ws.send(json.dumps(payload))
    print("📤 Suscripción enviada con éxito.", flush=True)

def iniciar_tracker():
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://stream.aisstream.io/v0/stream",
                on_open=on_open,
                on_message=on_message
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"⚠️ Error en websocket: {e}", flush=True)
        time.sleep(5)

# Arrancamos el hilo del tracker en segundo plano
hilo = threading.Thread(target=iniciar_tracker, daemon=True)
hilo.start()

@app.route('/datos')
def ver_datos():
    with lock:
        return jsonify(list(barcosguardados.values()))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
