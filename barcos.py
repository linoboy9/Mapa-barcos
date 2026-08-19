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

if not API_KEY:
    print("⚠️ ¡ALERTA! La variable de entorno 'AIS_API_KEY' NO está configurada en Render.")
else:
    print("✅ API Key detectada correctamente.")

barcosguardados = {}
lock = threading.Lock()

def on_message(ws, message):
    try:
        print(f"📥 Datos crudos recibidos del satélite: {message[:120]}...")
        datos = json.loads(message)
        if 'MetaData' in datos:
            barco = datos['MetaData']
            mmsi = barco.get('MMSI')
            if mmsi:
                with lock:
                    barcosguardados[mmsi] = barco
                    print(f"🚢 Barco guardado/actualizado: {barco.get('ShipName', 'Desconocido')} (MMSI: {mmsi})")
                    if len(barcosguardados) > 150:
                        viejo_mmsi = list(barcosguardados.keys())[0]
                        del barcosguardados[viejo_mmsi]
        else:
            print("⚠️ El mensaje no contiene 'MetaData'")
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")

def on_error(ws, error):
    print(f"❌ ERROR CRÍTICO en el WebSocket: {repr(error)}")

def on_open(ws):
    print("¡Conectado al satélite de AISStream! Enviando suscripción...")
    subscribe = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[-90, -180], [90, 180]]]
    }
    ws.send(json.dumps(subscribe))

def iniciar_tracker():
    while True:
        try:
            print("Intentando conectar al satélite...")
            ws = websocket.WebSocketApp(
                "wss://stream.aisstream.io/v0/stream",
                on_message=on_message,
                on_error=on_error,
                on_open=on_open
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"⚠️ Excepción general en el tracker: {e}")
        print("Reintentando conexión en 5 segundos...")
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
