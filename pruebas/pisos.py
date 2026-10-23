# Mini script de viabilidad: imprime 5 anuncios de alquiler de pisos.com
# AVISO: escrito con IA (Claude), declarado en el portafolio.
import time
import requests
from bs4 import BeautifulSoup

CIUDAD = "valencia_capital"
URL = f"https://www.pisos.com/alquiler/pisos-{CIUDAD}/"
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}


def leer_m2(anuncio):
    # Las características (habs., baños, m², planta) comparten la misma clase;
    # nos quedamos con la que termina en "m²"
    for car in anuncio.select("p.ad-preview__char"):
        texto = car.get_text(strip=True)
        if texto.endswith("m²"):
            return texto
    return "?"


respuesta = requests.get(URL, headers=CABECERAS, timeout=20)
print("Código de estado:", respuesta.status_code)

if respuesta.status_code == 200:
    sopa = BeautifulSoup(respuesta.text, "html.parser")
    anuncios = sopa.select("div.ad-preview")
    print("Anuncios en la página:", len(anuncios))

    for anuncio in anuncios[:5]:
        precio = anuncio.select_one(".ad-preview__price").get_text(" ", strip=True)
        barrio = anuncio.select_one(".ad-preview__subtitle").get_text(strip=True)
        enlace = anuncio.select_one("a.ad-preview__title")["href"]
        print(f"{precio:>14} | {leer_m2(anuncio):>7} | {barrio} | https://www.pisos.com{enlace}")

time.sleep(2)  # pausa de cortesía antes de cualquier otra petición
