# Archivo: scrapers/pisos.py
# Autor: Nicolás Roig Meseguer
# Fecha: 22/11/2026
# Qué hace: módulo de scraping de pisos.com para el programa principal (main.py).
#   obtener_anuncios(paginas) recorre las páginas del listado de viviendas en alquiler
#   de Valencia capital y devuelve los anuncios con las 11 columnas comunes.
#   Es la versión de pruebas/pisos.py convertida en función y con paginación.
# Uso de IA: Claude Opus 5.5 (Anthropic) adaptó pruebas/pisos.py a función y añadió
#   la paginación. Revisado y ejecutado por Nico.
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

PORTAL = "pisos"
# pisos.com redirige esta URL a .../pisos-valencia_capital_zona_urbana/,
# que es la misma página e incluye las pedanías (Benimàmet, El Perellonet...)
URL_PAGINA_1 = "https://www.pisos.com/alquiler/pisos-valencia_capital/"
# A partir de la página 2 la dirección es .../pisos-valencia_capital_zona_urbana/N/
# (es el enlace "Siguiente" de la web; robots.txt no prohíbe estas direcciones)
URL_PAGINA_N = "https://www.pisos.com/alquiler/pisos-valencia_capital_zona_urbana/{}/"
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}
PAUSA = 2  # segundos entre página y página, para no saturar la web

COLUMNAS = ["portal", "id_anuncio", "tipo", "precio", "m2", "habitaciones",
            "banos", "barrio", "distrito", "url", "fecha_recogida"]


def numero(texto):
    # "1.100 €/mes" -> 1100 ; "161 m²" -> 161 ; "4 habs." -> 4
    # Nos quedamos con la primera palabra, quitamos los puntos de miles y la pasamos a entero
    try:
        return int(texto.split()[0].replace(".", ""))
    except (ValueError, IndexError):
        return ""  # p. ej. "A consultar" o texto vacío: lo dejamos vacío, no nos lo inventamos


def leer_caracteristica(anuncio, palabra):
    # Habitaciones, baños, m² y planta comparten la misma clase y no siempre
    # aparecen todos, así que reconocemos cada dato por su texto, no por su posición
    for car in anuncio.find_all("p", class_="ad-preview__char"):
        texto = car.get_text(strip=True)
        if palabra in texto:
            return numero(texto)
    return ""


def leer_pagina(html):
    # Recibe el HTML de una página del listado y devuelve sus anuncios
    sopa = BeautifulSoup(html, "html.parser")
    hoy = date.today().strftime("%d/%m/%Y")
    anuncios_limpios = []

    for anuncio in sopa.find_all("div", class_="ad-preview"):
        titulo = anuncio.find("a", class_="ad-preview__title")
        precio = anuncio.find(class_="ad-preview__price")
        subtitulo = anuncio.find("p", class_="ad-preview__subtitle")
        if titulo is None or precio is None:
            continue  # tarjeta incompleta (publicidad...): la saltamos

        # El subtítulo es "Barrio (Distrito Nombre. València Capital)"
        barrio = ""
        distrito = ""
        if subtitulo is not None:
            ubicacion = subtitulo.get_text(strip=True)
            barrio = ubicacion.split(" (")[0]
            if "Distrito " in ubicacion:
                distrito = ubicacion.split("Distrito ")[1].split(".")[0]

        anuncios_limpios.append({
            "portal": PORTAL,
            # El id viene como "68397966198.101800": cambiamos el punto por "_" (como en la URL)
            # para que Excel no lo lea como un número y lo estropee
            "id_anuncio": anuncio.get("id", "").replace(".", "_"),
            "tipo": titulo.get_text(strip=True).split()[0].lower(),  # "Ático en ..." -> "ático"
            "precio": numero(precio.get_text(strip=True)),
            "m2": leer_caracteristica(anuncio, "m²"),
            "habitaciones": leer_caracteristica(anuncio, "hab"),
            "banos": leer_caracteristica(anuncio, "baño"),
            "barrio": barrio,
            "distrito": distrito,
            "url": "https://www.pisos.com" + titulo.get("href"),
            "fecha_recogida": hoy,
        })
    return anuncios_limpios


def hay_pagina_siguiente(html):
    # La última página del listado ya no tiene el enlace "Siguiente". Hay que mirarlo
    # porque pisos.com no da error al pedir una página que no existe: devuelve 200
    # con anuncios de relleno, siempre los mismos, y los cogeríamos repetidos
    sopa = BeautifulSoup(html, "html.parser")
    for enlace in sopa.find_all("a"):
        if enlace.get_text(strip=True) == "Siguiente":
            return True
    return False


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
        if not hay_pagina_siguiente(respuesta.text):
            break  # era la última página
    return todos


# Si se ejecuta este archivo solo (python scrapers/pisos.py), hace una prueba.
# Si lo importa main.py, esta parte no se ejecuta.
if __name__ == "__main__":
    resultado = obtener_anuncios(2)
    print("Total de anuncios:", len(resultado))
    for anuncio in resultado[:3]:
        print(anuncio)
