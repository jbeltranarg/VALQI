# Archivo: scrapers/habitaclia.py
# Autor: Javier Higuera Carrillo
# Fecha: 22/11/2026
# Qué hace: módulo de scraping de habitaclia para el programa principal (main.py).
#   obtener_anuncios(paginas) recorre las páginas del listado de viviendas en alquiler
#   de Valencia capital y devuelve los anuncios con las 11 columnas comunes.
#   Es la versión de pruebas/habitaclia.py convertida en función y con paginación.
# Uso de IA: Claude Opus 5.5 (Anthropic) adaptó pruebas/habitaclia.py a función, añadió
#   la paginación por ruta (/s/N) y comprobó la dirección de la página 2 y el robots.txt.
#   Revisado y ejecutado por Javier Higuera.
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

PORTAL = "habitaclia"
CIUDAD = "valencia-capital"
# /s al final = página 1
URL_PAGINA_1 = f"https://www.habitaclia.com/alquiler/viviendas/valencia-provincia/{CIUDAD}/s"
# A partir de la página 2 el número va en la ruta: .../s/2, .../s/3...
# (es la dirección del botón "2" de la web; robots.txt prohíbe ?pag= pero no esta ruta)
URL_PAGINA_N = URL_PAGINA_1 + "/{}"
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}
PAUSA = 2  # segundos entre página y página, para no saturar la web

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


def leer_pagina(html):
    # Recibe el HTML de una página del listado y devuelve sus anuncios
    sopa = BeautifulSoup(html, "html.parser")
    hoy = date.today().strftime("%d/%m/%Y")
    anuncios_limpios = []

    # Cada anuncio es un <article>
    for anuncio in sopa.find_all("article"):
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

        precio = buscar_dato(anuncio, "€/mes")
        if precio == "":
            continue  # sin precio el anuncio no sirve para comparar precios: lo saltamos

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
            "precio": precio,
            "m2": buscar_dato(anuncio, "m²"),
            "habitaciones": buscar_dato(anuncio, "hab"),
            "banos": buscar_dato(anuncio, "baño"),
            "barrio": barrio,
            "distrito": "",  # habitaclia no da el distrito en el listado: lo completa filtrado.py
            "url": url_anuncio,
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

        anuncios = leer_pagina(respuesta.text)
        print(f"  [{PORTAL}] página {pagina}: {len(anuncios)} anuncios")
        if len(anuncios) == 0:
            break  # no hay más páginas
        todos = todos + anuncios
    return todos


# Si se ejecuta este archivo solo (python scrapers/habitaclia.py), hace una prueba.
# Si lo importa main.py, esta parte no se ejecuta.
if __name__ == "__main__":
    resultado = obtener_anuncios(2)
    print("Total de anuncios:", len(resultado))
    for anuncio in resultado[:3]:
        print(anuncio)
