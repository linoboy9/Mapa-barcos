import websocket
import json
import threading
import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Esto es vital para que GitHub Pages no bloquee la conexión
CORS(app) 

API_KEY = "c9448c359fff4a189388f41f642c38861b9a73c5"

# Usamos un diccionario en memoria para guardar hasta 50 barcos simultáneos
barcos_guardados = {}

def on_message(ws, message):
    try:
        datos = json.loads(message)
        
        if 'error' in datos:
            print(f"❌ Error reportado por AIS Stream: {datos['error']}")
            return

        if 'MetaData' in datos:
            barco = datos['MetaData']
            mmsi = barco.get('MMSI') # ID único de cada barco
            
            if mmsi:
                barcos_guardados[mmsi] = barco
                
                if len(barcos_guardados) > 50:
                    viejo_mmsi = list(barcos_guardados.keys())[0]
                    del barcos_guardados[viejo_mmsi]

                print(f"🚢 Barco actualizado: {barco.get('ShipName', 'Desconocido')} | Lat: {barco.get('latitude')} | Lon: {barco.get('longitude')}")
                
    except Exception as e:
        print(f"⚠️ Error procesando el mensaje: {e}")

def on_open(ws):
    print("✅ ¡Conexión exitosa a aisstream.io! Enviando suscripción global...")
    subscribe = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[-90, -180], [90, 180]]]
    }
    ws.send(json.dumps(subscribe))

def on_error(ws, error):
    print(f"❌ Error en WebSocket de AIS Stream: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"🔒 Conexión de WebSocket cerrada. Código: {close_status_code}, Mensaje: {close_msg}")

def iniciar_tracker():
    import time
    while True:
        try:
            print("🔄 Intentando conectar al WebSocket de AIS Stream...")
            ws = websocket.WebSocketApp(
                "wss://stream.aisstream.io/v0/stream",
                on_message=on_message,
                on_open=on_open,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"⚠️ Error en el bucle del tracker: {e}")
        
        time.sleep(5)

# Arrancar el hilo automáticamente al cargar el módulo (funciona perfecto con Gunicorn en Render)
hilo = threading.Thread(target=iniciar_tracker, daemon=True)
hilo.start()

# --- RUTAS DEL SERVIDOR FLASK ---

@app.route('/')
def home():
    return "¡El backend de barcos está funcionando 24/7 en Render!"

@app.route('/datos')
def ver_datos():
    return jsonify(list(barcos_guardados.values()))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
