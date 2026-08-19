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

# --- DIAGNOSTICO DE CREDENCIALES ---
if API_KEY:
    print(f"🔑 API_KEY leída correctamente desde Render: {API_KEY[:4]}... (Longitud: {len(API_KEY)})", flush=True)
else:
    print("🚨 ¡ALERTA ROJA! AIS_API_KEY está VACÍA o NO EXISTE en las variables de entorno de Render.", flush=True)
# ----------------------------------

barcosguardados = {}
lock = threading.Lock()

def on_message(ws, message):
    print(f"📥 ¡MENSAJE RECIBIDO!: {message[:300]}", flush=True)
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
                    print(f"🚢 Barco guardado: {nombre} | Lat: {lat} | Lon: {lon}", flush=True)
                    if len(barcosguardados) > 300:
                        viejo_mmsi = list(barcosguardados.keys())[0]
                        del barcosguardados[viejo_mmsi]
    except Exception as e:
        print(f"❌ Error procesando JSON: {e}", flush=True)

def on_error(ws, error):
    print(f"❌ ERROR EN SOCKET: {repr(error)}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print(f"🔌 Socket cerrado. Código: {close_status_code} - Msg: {close_msg}", flush=True)

def on_open(ws):
    if not API_KEY:
        print("❌ Imposible suscribirse: La API Key es nula.", flush=True)
        return
    print("🟢 Conexión abierta. Enviando suscripción...", flush=True)
    payload = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[50.0, 2.0], [54.0, 7.0]]]
    }
    ws.send(json.dumps(payload))
    print("📤 Suscripción enviada. Esperando flujo del satélite...", flush=True)

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
            print(f"⚠️ Excepción general: {e}", flush=True)
        print("⏳ Reiniciando ciclo en 5 segundos...", flush=True)
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
