# Archivo: pruebas/ayuntamiento.py
# Autor: Persona D (Dani)
# Fecha: 28/10/2026
# Qué hace: descarga de la API de datos abiertos del Ayuntamiento de Valencia
#   los barrios oficiales (Geoportal) y su población (portal CKAN), los junta
#   por el nombre del barrio, imprime 5 y guarda todo en CSV.
# Uso de IA: código escrito con IA (Claude) y revisado línea a línea por Dani.
#   Declarado en el portafolio.

import csv
from datetime import date

import requests

CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}
COLUMNAS = ["fuente", "codigo_distrito", "distrito", "codigo_barrio", "barrio",
            "poblacion", "fecha_recogida"]

URL_BARRIOS = "https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/224/query"
PARAMETROS_BARRIOS = {
    "where": "1=1",             
    "outFields": "*",           
    "returnGeometry": "false", 
    "f": "json",                
}

URL_POBLACION = "https://opendata.vlci.valencia.es/api/3/action/datastore_search"
PARAMETROS_POBLACION = {
    "resource_id": "6810cb63-d55c-4ffa-9b5d-5dcbbdce171c",  
    "limit": 1000,              
}

resp_barrios = requests.get(URL_BARRIOS, headers=CABECERAS, params=PARAMETROS_BARRIOS, timeout=20)
resp_poblacion = requests.get(URL_POBLACION, headers=CABECERAS, params=PARAMETROS_POBLACION, timeout=20)

print("Fuente: API de datos abiertos del Ayuntamiento de Valencia")
print("URL barrios:", resp_barrios.url)
print("Código de estado barrios:", resp_barrios.status_code)
print("URL población:", resp_poblacion.url)
print("Código de estado población:", resp_poblacion.status_code)

if resp_barrios.status_code == 200 and resp_poblacion.status_code == 200:
    hoy = date.today().strftime("%d/%m/%Y")
    info_barrio = {}
    for registro in resp_poblacion.json()["result"]["records"]:
        if registro["GRUPOS"] == "Grupo 2":
            nombre = registro["BARRIO"].strip()
            clave = nombre.replace("-", "")
            info_barrio[clave] = {
                "distrito": registro["DISTRITO"].strip(),
                "poblacion": int(registro["HABITANTES"]),  
            }

    barrios = []
    no_encontrados = []
    for elemento in resp_barrios.json()["features"]:  
        atributos = elemento["attributes"]           
        nombre = atributos["nombre"].strip()
        clave = nombre.replace("-", "")

        distrito = ""
        poblacion = ""
        if clave in info_barrio:
            distrito = info_barrio[clave]["distrito"]
            poblacion = info_barrio[clave]["poblacion"]
        else:
            no_encontrados.append(nombre)

        barrio = {
            "fuente": "ayuntamiento",
            "codigo_distrito": atributos["coddistrit"],
            "distrito": distrito,
            "codigo_barrio": atributos["coddistbar"],  
            "barrio": nombre,
            "poblacion": poblacion,
            "fecha_recogida": hoy,
        }
        barrios.append(barrio)

    print("Barrios obtenidos:", len(barrios))
    print("Barrios sin población (nombre distinto en los dos datasets):", no_encontrados)

    numero = 1
    for barrio in barrios[:5]:
        print(f"--- Barrio {numero} ---")
        for columna in COLUMNAS:
            print(f"{columna}: {barrio[columna]}")
        numero = numero + 1

    with open("data/D_ayuntamiento_barrios.csv", "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(COLUMNAS)
        for barrio in barrios:
            fila = []
            for columna in COLUMNAS:
                fila.append(barrio[columna])
            escritor.writerow(fila)
    print("CSV guardado")
else:
    print("Aviso: alguna de las dos APIs no ha respondido bien. No sigo.")