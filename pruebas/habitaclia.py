# Mini script de viabilidad: imprime 5 anuncios de alquiler de habitaclia.com
# AVISO: escrito con IA (Claude), declarado en el portafolio.
import time
import requests
from bs4 import BeautifulSoup

CIUDAD = "valencia-capital"
URL = f"https://www.habitaclia.com/alquiler/viviendas/valencia-provincia/{CIUDAD}/s"
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}


def buscar_texto(anuncio, final):
    # habitaclia usa clases CSS genéricas (Tailwind) que no identifican cada dato,
    # así que buscamos el primer <span> cuyo texto termine de una forma concreta
    for span in anuncio.find_all("span"):
        texto = span.get_text(strip=True)
        if texto.endswith(final):
            return texto
    return "?"


respuesta = requests.get(URL, headers=CABECERAS, timeout=20)
print("Código de estado:", respuesta.status_code)

if respuesta.status_code == 200:
    sopa = BeautifulSoup(respuesta.text, "html.parser")
    anuncios = sopa.find_all("article")
    print("Anuncios en la página:", len(anuncios))

    for anuncio in anuncios[:5]:
        precio = buscar_texto(anuncio, "€/mes")
        m2 = buscar_texto(anuncio, "m²")
        enlace = anuncio.find("a", attrs={"data-panot-component": "link-box-link"})["href"]
        # No todos los anuncios muestran el barrio en el texto, pero la URL siempre
        # lo lleva justo antes de la ciudad: .../camins-al-grau/valencia-capital/...
        partes = enlace.split("/")
        barrio = partes[partes.index(CIUDAD) - 1]
        print(f"{precio:>12} | {m2:>7} | {barrio} | https://www.habitaclia.com{enlace}")

time.sleep(2)  # pausa de cortesía antes de cualquier otra petición
