# Archivo: scrapers/enalquiler.py
# Autor: Javier Beltrán Argente
# Fecha: 21/11/2026
# Qué hace: módulo de scraping de Enalquiler para el programa principal (main.py).
#   obtener_anuncios(paginas) recorre las páginas del listado de pisos en alquiler
#   de Valencia capital y devuelve los anuncios con las 11 columnas comunes.
#   Es la versión de pruebas/enalquiler.py convertida en función y con paginación.
# Uso de IA: Claude Opus 5.5 (Anthropic) adaptó pruebas/enalquiler.py a función y añadió
#   la paginación. Revisado y ejecutado por Javi.
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

PORTAL = "enalquiler"
# En la dirección: 48 = provincia de Valencia, 2 = pisos, 50692 = municipio de Valencia
URL_PAGINA_1 = "https://www.enalquiler.com/alquiler-pisos-valencia-48-2-0-50692.html"
# A partir de la página 2 la dirección cambia: .../alquiler-pisos-valencia_48_50692_2/N
# (robots.txt no prohíbe estas direcciones)
URL_PAGINA_N = "https://www.enalquiler.com/alquiler-pisos-valencia_48_50692_2/{}"
TIPO = "piso"  # esta búsqueda solo trae pisos
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}
PAUSA = 2  # segundos entre página y página, para no saturar la web

COLUMNAS = ["portal", "id_anuncio", "tipo", "precio", "m2", "habitaciones",
            "banos", "barrio", "distrito", "url", "fecha_recogida"]


def numero(texto):
    # "2.300€" -> 2300 ; "161m2" -> 161 ; "4 Hab" -> 4
    texto = texto.replace("€", "").replace("m2", "").replace(".", "")
    try:
        return int(texto.split()[0])
    except (ValueError, IndexError):
        return ""  # si no es un número, lo dejamos vacío: no nos lo inventamos


def leer_detalle(detalles, palabra):
    # m², habitaciones y baños van cada uno en un <li>, pero no siempre aparecen
    # todos, así que reconocemos cada dato por su texto y no por su posición
    if detalles is None:
        return ""
    for li in detalles.find_all("li"):
        texto = li.get_text(strip=True)
        if palabra in texto:
            return numero(texto)
    return ""


def leer_pagina(html):
    # Recibe el HTML de una página del listado y devuelve sus anuncios
    sopa = BeautifulSoup(html, "html.parser")
    hoy = date.today().strftime("%d/%m/%Y")
    anuncios_limpios = []

    for anuncio in sopa.find_all("li", class_="propertyCard"):
        precio = anuncio.find("span", class_="propertyCard__price--value")
        detalles = anuncio.find("ul", class_="propertyCard__details")
        enlace = anuncio.find("a", class_="propertyCard__description--title")
        lugar = anuncio.find("div", class_="propertyCard__location")
        if precio is None or enlace is None or lugar is None:
            continue  # tarjeta incompleta (publicidad...): la saltamos

        # La ubicación es "[calle,] distrito, barrio, Valencia": la leemos desde el final
        partes = lugar.get_text(strip=True).split(",")
        barrio = ""
        distrito = ""
        if len(partes) >= 2:
            barrio = partes[-2].strip()
        if len(partes) >= 3:
            distrito = partes[-3].strip()

        anuncios_limpios.append({
            "portal": PORTAL,
            "id_anuncio": anuncio.get("list-item"),
            "tipo": TIPO,
            "precio": numero(precio.get_text(strip=True)),
            "m2": leer_detalle(detalles, "m2"),
            "habitaciones": leer_detalle(detalles, "Hab"),
            "banos": leer_detalle(detalles, "Baño"),
            "barrio": barrio,
            "distrito": distrito,
            "url": enlace.get("href"),
            "fecha_recogida": hoy,
        })
    return anuncios_limpios


def obtener_anuncios(paginas=1):
    # Función que llama main.py: descarga 'paginas' páginas y devuelve todos los anuncios
    todos = []
    for pagina in range(1, paginas + 1):
        if pagina == 1:
            url = URL_PAGINA_1
        else:
            url = URL_PAGINA_N.format(pagina)
            time.sleep(PAUSA)

        respuesta = requests.get(url, headers=CABECERAS, timeout=20)
        if respuesta.status_code != 200:
            print(f"  [{PORTAL}] página {pagina}: código {respuesta.status_code}, paro aquí")
            break
        # La web declara ISO-8859-1 pero escribe el € en cp1252 (ver pruebas/enalquiler.py)
        respuesta.encoding = "cp1252"

        anuncios = leer_pagina(respuesta.text)
        print(f"  [{PORTAL}] página {pagina}: {len(anuncios)} anuncios")
        if len(anuncios) == 0:
            break  # no hay más páginas
        todos = todos + anuncios
    return todos


# Si se ejecuta este archivo solo (python scrapers/enalquiler.py), hace una prueba.
# Si lo importa main.py, esta parte no se ejecuta.
if __name__ == "__main__":
    resultado = obtener_anuncios(2)
    print("Total de anuncios:", len(resultado))
    for anuncio in resultado[:3]:
        print(anuncio)
