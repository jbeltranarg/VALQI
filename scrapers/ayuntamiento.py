# Archivo: scrapers/ayuntamiento.py
# Autor: Daniel Vidal Penades
# Fecha: 22/11/2026
# Qué hace: módulo de la API de datos abiertos del Ayuntamiento de Valencia para el
#   programa principal (main.py). obtener_barrios() descarga los barrios oficiales
#   (Geoportal) y su población (portal CKAN), los junta por el nombre del barrio y
#   devuelve la lista de barrios con 7 columnas. Es la versión de
#   pruebas/ayuntamiento.py convertida en función.
# Uso de IA: Claude Opus 5.5 (Anthropic) adaptó pruebas/ayuntamiento.py a función,
#   quitó el CSV y los print de prueba y añadió las líneas de progreso. Revisado y
#   ejecutado por Dani.
from datetime import date

import requests

FUENTE = "ayuntamiento"
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}
COLUMNAS = ["fuente", "codigo_distrito", "distrito", "codigo_barrio", "barrio",
            "poblacion", "fecha_recogida"]

# Barrios oficiales: capa 224 del Geoportal (ArcGIS). No es una página web sino una
# API que devuelve JSON, así que no hace falta BeautifulSoup.
URL_BARRIOS = "https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/224/query"
PARAMETROS_BARRIOS = {
    "where": "1=1",             # sin filtro: queremos todos los barrios
    "outFields": "*",           # todos los campos (nombre, códigos...)
    "returnGeometry": "false",  # no queremos el dibujo del mapa, solo los datos
    "f": "json",                # que la respuesta venga en JSON
}

# Población por barrio: portal CKAN de datos abiertos (opendata.vlci.valencia.es)
URL_POBLACION = "https://opendata.vlci.valencia.es/api/3/action/datastore_search"
PARAMETROS_POBLACION = {
    "resource_id": "6810cb63-d55c-4ffa-9b5d-5dcbbdce171c",  # dataset de población por barrio
    "limit": 1000,              # de sobra para que vengan todos los registros de una vez
}


def obtener_barrios():
    # Función que llama main.py: devuelve los barrios oficiales con su población.
    # Solo son 2 peticiones, así que no hay paginación ni pausa.
    resp_barrios = requests.get(URL_BARRIOS, headers=CABECERAS,
                                params=PARAMETROS_BARRIOS, timeout=20)
    resp_poblacion = requests.get(URL_POBLACION, headers=CABECERAS,
                                  params=PARAMETROS_POBLACION, timeout=20)

    # Si alguna API falla, devolvemos una lista vacía: main.py lo comprueba y para
    if resp_barrios.status_code != 200 or resp_poblacion.status_code != 200:
        print(f"  [{FUENTE}] aviso: barrios código {resp_barrios.status_code}, "
              f"población código {resp_poblacion.status_code}. No sigo.")
        return []

    hoy = date.today().strftime("%d/%m/%Y")

    # 1. Población: diccionario {nombre del barrio sin guiones: distrito y población}.
    #    Quitamos los guiones porque un dataset escribe "MONTOLIVET" y el otro
    #    "MONT-OLIVET". Solo nos interesan los registros de "Grupo 2" (barrios).
    info_barrio = {}
    for registro in resp_poblacion.json()["result"]["records"]:
        if registro["GRUPOS"] == "Grupo 2":
            nombre = registro["BARRIO"].strip()
            clave = nombre.replace("-", "")
            info_barrio[clave] = {
                "distrito": registro["DISTRITO"].strip(),
                "poblacion": int(registro["HABITANTES"]),  # viene como texto: lo pasamos a número
            }

    # 2. Barrios oficiales del Geoportal: les añadimos el distrito y la población
    barrios = []
    no_encontrados = []
    for elemento in resp_barrios.json()["features"]:  # cada "feature" es un barrio
        atributos = elemento["attributes"]           # sus datos están en "attributes"
        nombre = atributos["nombre"].strip()
        clave = nombre.replace("-", "")

        # Si el barrio no está en el dataset de población, lo dejamos vacío: no lo inventamos
        distrito = ""
        poblacion = ""
        if clave in info_barrio:
            distrito = info_barrio[clave]["distrito"]
            poblacion = info_barrio[clave]["poblacion"]
        else:
            no_encontrados.append(nombre)

        barrios.append({
            "fuente": FUENTE,
            "codigo_distrito": atributos["coddistrit"],
            "distrito": distrito,
            "codigo_barrio": atributos["coddistbar"],
            "barrio": nombre,
            "poblacion": poblacion,
            "fecha_recogida": hoy,
        })

    print(f"  [{FUENTE}] barrios: {len(barrios)} (código {resp_barrios.status_code})")
    print(f"  [{FUENTE}] barrios sin población: {len(no_encontrados)}")
    return barrios


# Si se ejecuta este archivo solo (python3 scrapers/ayuntamiento.py), hace una prueba.
# Si lo importa main.py, esta parte no se ejecuta.
if __name__ == "__main__":
    resultado = obtener_barrios()
    print("Total de barrios:", len(resultado))
    for barrio in resultado[:3]:
        print(barrio)
