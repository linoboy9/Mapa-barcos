import json

def obtener_datos_barcos():
    barcos_ejemplo = [
        {"nombre": "MSC Emma", "lat": 25.123, "lon": -45.789, "carga": "Contenedores"},
        {"nombre": "Maersk Mc-Kinney", "lat": -12.456, "lon": 80.123, "carga": "Electrónica"},
        {"nombre": "CMA CGM Jacques", "lat": 35.890, "lon": -10.345, "carga": "Alimentos"}
    ]
    return barcos_ejemplo

def actualizar_mapa():
    datos = obtener_datos_barcos()
    with open("posiciones.json", "w") as archivo:
        json.dump(datos, archivo, indent=4)
    print("Posiciones de barcos actualizadas con éxito.")

if __name__ == "__main__":
    actualizar_mapa()
