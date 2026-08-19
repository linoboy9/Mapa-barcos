import encodings.idna
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
            lat = meta.get('latitude')
            lon = meta.get('longitude')
            if mmsi and lat is not None and lon is not None:
                with lock:
                    barcosguardados[mmsi] = meta
                    if len(barcosguardados) > 250:
                        del barcosguardados[next(iter(barcosguardados))]
                    print(f"🚢 {meta.get('ShipName', 'Barco').strip()} | {lat}, {lon}", flush=True)
    except Exception as e:
        print(f"Error mensaje: {e}", flush=True)

def on_error(ws, error):
    print(f"Error WebSocket: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print(f"Conexión cerrada: {close_status_code}", flush=True)

def on_open(ws):
    # Enviar la suscripción lo más rápido posible (menos de 3 segundos)
    payload = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[50.0, -5.0], [52.0, 2.0]]]
    }
    ws.send(json.dumps(payload))
    print("Suscripción enviada correctamente", flush=True)

def iniciar_tracker():
    while True:
        try:
            print("Conectando a AISStream...", flush=True)
            ws = websocket.WebSocketApp(
                "wss://stream.aisstream.io/v0/stream",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as e:
            print(f"Error tracker: {e}", flush=True)
        time.sleep(5)

hilo = threading.Thread(target=iniciar_tracker, daemon=True)
hilo.start()

@app.route('/')
def home():
    return "API de barcos funcionando. Usa /datos"

@app.route('/datos')
def ver_datos():
    with lock:
        return jsonify(list(barcosguardados.values()))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
