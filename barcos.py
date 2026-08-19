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
        print(f"📥 ¡DATOS RECIBIDOS!: {message[:200]}", flush=True)
        datos = json.loads(message)
        if 'MetaData' in datos:
            barco = datos['MetaData']
            mmsi = barco.get('MMSI')
            if mmsi:
                with lock:
                    barcosguardados[mmsi] = barco
                    print(f"🚢 ¡BARCO GUARDADO! MMSI: {mmsi} - Nombre: {barco.get('ShipName', 'Desconocido')}", flush=True)
                    if len(barcosguardados) > 150:
                        viejo_mmsi = list(barcosguardados.keys())[0]
                        del barcosguardados[viejo_mmsi]
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}", flush=True)

def on_error(ws, error):
    print(f"❌ ERROR EN WEBSOCKET: {repr(error)}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print(f"🔌 Conexión cerrada. Código: {close_status_code}, Mensaje: {close_msg}", flush=True)

def on_open(ws):
    print("¡Conectado al satélite! Enviando suscripción regional...", flush=True)
    # Acotamos a la zona del Caribe y Atlántico/Golfo para garantizar flujo inmediato de barcos
    subscribe = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[8.0, -90.0], [30.0, -60.0]]]
    }
    ws.send(json.dumps(subscribe))
    print("📤 ¡Suscripción enviada al satélite!", flush=True)

def iniciar_tracker():
    while True:
        try:
            print("Intentando conectar al satélite...", flush=True)
            ws = websocket.WebSocketApp(
                "wss://stream.aisstream.io/v0/stream",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"⚠️ Excepción general en el tracker: {e}", flush=True)
        print("Reintentando conexión en 5 segundos...", flush=True)
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
