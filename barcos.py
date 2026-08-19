import asyncio
import json
import os
import threading
import websockets
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Simplificado para evitar cualquier error de sintaxis

API_KEY = os.environ.get("AIS_API_KEY")

barcosguardados = {}
lock = threading.Lock()

async def ais_listener():
    uri = "wss://stream.aisstream.io/v0/stream"
    while True:
        try:
            print("🔄 Conectando a AISStream (async)...", flush=True)
            async with websockets.connect(uri) as websocket:
                subscribe_message = {
                    "APIKey": API_KEY,
                    # Caja regional del Mar del Norte y Países Bajos (tráfico masivo)
                    "BoundingBoxes": [
                        [
                            [50.0, 2.0],
                            [54.0, 7.0]
                        ]
                    ],
                    "FilterMessageTypes": ["PositionReport"]
                }
                await websocket.send(json.dumps(subscribe_message))
                print("🟢 Suscripción enviada con éxito. Esperando barcos...", flush=True)

                async for message in websocket:
                    data = json.loads(message)
                    meta = data.get("MetaData", {})
                    mmsi = meta.get("MMSI")
                    nombre = meta.get("ShipName", "Desconocido").strip()
                    lat = meta.get("latitude")
                    lon = meta.get("longitude")

                    if mmsi and lat is not None and lon is not None:
                        with lock:
                            barcosguardados[mmsi] = meta
                            print(f"Barco: {nombre} | Lat: {lat} | Lon: {lon}", flush=True)
                            
                            # Mantenemos un límite de 300 barcos en memoria para no saturar
                            if len(barcosguardados) > 300:
                                viejo_mmsi = list(barcosguardados.keys())[0]
                                del barcosguardados[viejo_mmsi]
        except Exception as e:
            print(f"⚠️ Error en websocket: {e}", flush=True)
            await asyncio.sleep(5)

def run_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ais_listener())

# Arrancamos el oyente asíncrono en segundo plano
hilo = threading.Thread(target=run_async_loop, daemon=True)
hilo.start()

@app.route('/datos')
def ver_datos():
    with lock:
        return jsonify(list(barcosguardados.values()))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
