import encodings.idna
import websocket
import json
import threading
import os
import time
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

API_KEY = os.environ.get("AIS_API_KEY")

barcosguardados = {}
lock = threading.Lock()

def on_message(ws, message):
    try:
        datos = json.loads(message)
        # AISStream envía la data dentro de un campo 'Message'
        if 'Message' in datos and 'PositionReport' in datos['Message']:
            pos = datos['Message']['PositionReport']
            meta = datos['MetaData']
            mmsi = meta.get('MMSI')
            nombre = meta.get('ShipName', 'Desconocido').strip()
            lat = meta.get('latitude')
            lon = meta.get('longitude')
            
            if mmsi and lat is not None and lon is not None:
                with lock:
                    barcosguardados[mmsi] = {
                        "MMSI": mmsi,
                        "ShipName": nombre,
                        "latitude": lat,
                        "longitude": lon,
                        "time": meta.get('time_utc')
                    }
                    print(f"Barco: {nombre} | Lat: {lat} | Lon: {lon}", flush=True)
                    if len(barcosguardados) > 300:
                        viejo_mmsi = list(barcosguardados.keys())[0]
                        del barcosguardados[viejo_mmsi]
    except Exception as e:
        print(f"❌ Error al procesar JSON: {e}", flush=True)

def on_error(ws, error):
    print(f"❌ Error en socket: {repr(error)}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print("🔌 Socket cerrado por el servidor.", flush=True)

def on_open(ws):
    print("🟢 Conectado. Enviando suscripción oficial...", flush=True)
    # Estructura exacta requerida por la API de AisStream
    payload = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[-90, -180], [90, 180]]],
        "FilterMessageTypes": ["PositionReport"]
    }
    ws.send(json.dumps(payload))
    print("📤 Suscripción enviada correctamente.", flush=True)

def iniciar_tracker():
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://stream.aisstream.io/v0/stream",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"⚠️ Error crítico: {e}", flush=True)
        time.sleep(5)

hilo = threading.Thread(target=iniciar_tracker, daemon=True)
hilo.start()

@app.route('/datos')
def ver_datos():
    with lock:
        return jsonify(list(barcosguardados.values()))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
