# Archivo: pruebas/habitaclia.py
# Autor: Persona C (Javier Higuera)
# Fecha: 31/10/2026
# Qué hace: descarga la página 1 de viviendas en alquiler de Valencia capital en habitaclia,
#   extrae las columnas comunes de cada anuncio, imprime 5 y guarda la página en CSV.
# Uso de IA: Claude Opus 5.5 propuso la estructura a partir de la prueba de viabilidad de B.
#   Revisado y probado por Javier.
import csv
from datetime import date

import requests
from bs4 import BeautifulSoup

PORTAL = "habitaclia"
CIUDAD = "valencia-capital"
# /s al final = página 1. La página N sería .../s/N (el parámetro ?pag= lo prohíbe robots.txt)
URL = f"https://www.habitaclia.com/alquiler/viviendas/valencia-provincia/{CIUDAD}/s"
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}

COLUMNAS = ["portal", "id_anuncio", "tipo", "precio", "m2", "habitaciones",
            "banos", "barrio", "distrito", "url", "fecha_recogida"]


def numero(texto):
    # "1.300 €/mes" -> 1300 ; "88 m²" -> 88 ; "3 habs." -> 3
    # Quitamos los símbolos y los puntos de miles, cogemos la primera palabra y la pasamos a entero
    texto = texto.replace("€/mes", "").replace("€", "").replace("m²", "").replace(".", "")
    try:
        return int(texto.split()[0])
    except (ValueError, IndexError):
        return ""  # si no es un número, lo dejamos vacío: no nos lo inventamos


def buscar_dato(anuncio, palabra):
    # habitaclia usa clases CSS genéricas que no dicen qué dato hay dentro,
    # así que recorremos los <span> y reconocemos el dato por su texto.
    # Solo miramos los <span> que no tienen otro <span> dentro: si no, un <span>
    # grande que junta "88 m²3 habs." nos daría un número equivocado
    for span in anuncio.find_all("span"):
        if span.find("span") is None:
            texto = span.get_text(strip=True)
            if palabra in texto:
                valor = numero(texto)
                if valor != "":
                    return valor  # si el texto no empieza por un número, seguimos buscando
    return ""


# Paso 1: descargar la página (una sola petición)
respuesta = requests.get(URL, headers=CABECERAS, timeout=20)
if respuesta.status_code != 200:
    print("Aviso: la web ha devuelto el código", respuesta.status_code)
    exit()

# Paso 2: encontrar los anuncios (cada anuncio es un <article>)
sopa = BeautifulSoup(respuesta.text, "html.parser")
anuncios = sopa.find_all("article")

# Pasos 3 y 4: sacar cada columna y dejarla en el formato común
hoy = date.today().strftime("%d/%m/%Y")
anuncios_limpios = []

for anuncio in anuncios:
    # El enlace al anuncio es el <a> cuya dirección contiene la ciudad
    # (find_all("a") + .get("href"), como en clase)
    enlace = None
    for a in anuncio.find_all("a"):
        href = a.get("href")
        if href is not None and CIUDAD in href:
            enlace = a
            break
    if enlace is None:
        continue  # no es un anuncio de vivienda (publicidad, banner...): lo saltamos

    href = enlace.get("href").split("?")[0]  # quitamos lo que va tras "?" (datos de seguimiento)
    if href.startswith("/"):
        url_anuncio = "https://www.habitaclia.com" + href  # la dirección viene sin el dominio
    else:
        url_anuncio = href

    # La dirección es .../extramurs/valencia-capital/788dcb21-df7e-.../d
    # justo antes de la ciudad va el barrio y justo después, el código del anuncio
    partes = href.split("/")
    barrio = ""
    id_anuncio = ""
    if CIUDAD in partes:
        posicion = partes.index(CIUDAD)
        barrio = partes[posicion - 1]
        id_anuncio = partes[posicion + 1]

    # El texto del enlace es el título: "Piso en Calle ..." -> "piso"
    titulo = enlace.get_text(strip=True)
    tipo = ""
    if titulo != "":
        tipo = titulo.split()[0].lower()

    anuncios_limpios.append({
        "portal": PORTAL,
        "id_anuncio": id_anuncio,
        "tipo": tipo,
        "precio": buscar_dato(anuncio, "€/mes"),
        "m2": buscar_dato(anuncio, "m²"),
        "habitaciones": buscar_dato(anuncio, "hab"),
        "banos": buscar_dato(anuncio, "baño"),
        "barrio": barrio,
        "distrito": "",  # habitaclia no da el distrito en el listado: se completa en la limpieza
        "url": url_anuncio,
        "fecha_recogida": hoy,
    })

# Paso 5: imprimir con el formato común
print("Portal:", PORTAL)
print("URL:", URL)
print("Código de estado:", respuesta.status_code)
print("Anuncios en la página:", len(anuncios_limpios))

# Mostramos los 5 primeros con todas las columnas
numero_anuncio = 1
for anuncio in anuncios_limpios[:5]:
    print(f"--- Anuncio {numero_anuncio} ---")
    for columna in COLUMNAS:
        print(f"{columna}: {anuncio[columna]}")
    numero_anuncio = numero_anuncio + 1

# Paso 6: guardar la página en CSV
# data/ está en el .gitignore: el CSV nunca se sube al repositorio
with open("data/C_habitaclia_muestra.csv", "w", newline="", encoding="utf-8-sig") as f:
    escritor = csv.writer(f, delimiter=";")
    escritor.writerow(COLUMNAS)
    for anuncio in anuncios_limpios:
        fila = []
        for columna in COLUMNAS:
            fila.append(anuncio[columna])
        escritor.writerow(fila)
print("CSV guardado")
