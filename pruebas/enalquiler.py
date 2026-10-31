# Archivo: pruebas/enalquiler.py
# Autor: Persona A (Javi)
# Fecha: 30/10/2026
# Qué hace: descarga la página 1 de pisos en alquiler de Valencia capital en Enalquiler,
#   extrae las columnas comunes de cada anuncio, imprime 5 y guarda la página en CSV.
# Uso de IA: (pendiente de rellenar)
import csv
from datetime import date

import requests
from bs4 import BeautifulSoup

PORTAL = "enalquiler"
# En la dirección: 48 = provincia de Valencia, 2 = pisos, 50692 = municipio de Valencia
URL = "https://www.enalquiler.com/alquiler-pisos-valencia-48-2-0-50692.html"
TIPO = "piso"  # sale del código 2 de la dirección: esta búsqueda solo trae pisos
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}

COLUMNAS = ["portal", "id_anuncio", "tipo", "precio", "m2", "habitaciones",
            "banos", "barrio", "distrito", "url", "fecha_recogida"]


def numero(texto):
    # "2.300€" -> 2300 ; "161m2" -> 161 ; "4 Hab" -> 4
    # Quitamos el símbolo €, el "m2" y los puntos de miles, cogemos la primera palabra
    # y la pasamos a entero
    texto = texto.replace("€", "").replace("m2", "").replace(".", "")
    try:
        return int(texto.split()[0])
    except ValueError:
        return ""  # si no es un número, lo dejamos vacío: no nos lo inventamos


def leer_detalle(detalles, palabra):
    # Los m², habitaciones y baños van cada uno en un <li>, pero no siempre aparecen
    # todos (a veces en su lugar sale "Piso"), así que reconocemos cada dato por su
    # texto y no por su posición
    for li in detalles.find_all("li"):
        texto = li.get_text(strip=True)
        if palabra in texto:
            return numero(texto)
    return ""


# Paso 1: descargar la página (una sola petición)
respuesta = requests.get(URL, headers=CABECERAS, timeout=20)
if respuesta.status_code != 200:
    print("Aviso: la web ha devuelto el código", respuesta.status_code)
    exit()

# La web dice que su codificación es ISO-8859-1, pero el símbolo € lo escribe con el
# código de Windows-1252 (cp1252). Si no lo corregimos, el € sale como un carácter
# raro y el precio no se puede convertir a número (lo vimos en la UD1: emisor y
# receptor tienen que ponerse de acuerdo en la codificación)
respuesta.encoding = "cp1252"

# Paso 2: encontrar los anuncios (cada anuncio es un <li class="propertyCard">)
sopa = BeautifulSoup(respuesta.text, "html.parser")
anuncios = sopa.find_all("li", class_="propertyCard")

# Pasos 3 y 4: sacar cada columna y dejarla en el formato común
hoy = date.today().strftime("%d/%m/%Y")
anuncios_limpios = []

for anuncio in anuncios:
    precio = anuncio.find("span", class_="propertyCard__price--value").get_text(strip=True)
    detalles = anuncio.find("ul", class_="propertyCard__details")
    enlace = anuncio.find("a", class_="propertyCard__description--title")

    # La ubicación es "[calle,] distrito, barrio, Valencia". A veces empieza por la
    # calle, así que la leemos desde el final: [-1] ciudad, [-2] barrio, [-3] distrito
    ubicacion = anuncio.find("div", class_="propertyCard__location").get_text(strip=True)
    partes = ubicacion.split(",")
    barrio = ""
    distrito = ""
    if len(partes) >= 2:
        barrio = partes[-2].strip()
    if len(partes) >= 3:
        distrito = partes[-3].strip()

    anuncios_limpios.append({
        "portal": PORTAL,
        "id_anuncio": anuncio.get("list-item"),  # número del anuncio, en un atributo del <li>
        "tipo": TIPO,
        "precio": numero(precio),
        "m2": leer_detalle(detalles, "m2"),
        "habitaciones": leer_detalle(detalles, "Hab"),
        "banos": leer_detalle(detalles, "Baño"),
        "barrio": barrio,
        "distrito": distrito,
        "url": enlace.get("href"),  # la dirección ya viene completa
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
with open("data/A_enalquiler_muestra.csv", "w", newline="", encoding="utf-8-sig") as f:
    escritor = csv.writer(f, delimiter=";")
    escritor.writerow(COLUMNAS)
    for anuncio in anuncios_limpios:
        fila = []
        for columna in COLUMNAS:
            fila.append(anuncio[columna])
        escritor.writerow(fila)
print("CSV guardado")
