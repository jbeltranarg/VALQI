# Prueba de viabilidad de pisos.com (Persona B, VALQI)
# Imprime 5 anuncios de alquiler de Valencia capital con precio, m², barrio y URL.
# USO DE IA: script escrito por Claude Opus 5.5 (estructura, selectores y la función leer_m2).
import requests
from bs4 import BeautifulSoup

# pisos.com redirige esta URL a .../pisos-valencia_capital_zona_urbana/,
# que es la misma página e incluye las pedanías (Benimàmet, El Perellonet...)
CIUDAD = "valencia_capital"
URL = f"https://www.pisos.com/alquiler/pisos-{CIUDAD}/"
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}


def leer_m2(anuncio):
    # Las características (habs., baños, m², planta) comparten la misma clase;
    # nos quedamos con la que termina en "m²"
    for car in anuncio.find_all("p", class_="ad-preview__char"):
        texto = car.get_text(strip=True)
        if texto.endswith("m²"):
            return texto
    return "?"


respuesta = requests.get(URL, headers=CABECERAS, timeout=20)
print("Código de estado:", respuesta.status_code)

if respuesta.status_code == 200:
    sopa = BeautifulSoup(respuesta.text, "html.parser")
    anuncios = sopa.find_all("div", class_="ad-preview")
    print("Anuncios en la página:", len(anuncios))

    for anuncio in anuncios[:5]:
        precio = anuncio.find(class_="ad-preview__price").get_text(" ", strip=True)
        barrio = anuncio.find("p", class_="ad-preview__subtitle").get_text(strip=True)
        enlace = anuncio.find("a", class_="ad-preview__title")["href"]
        print(precio, "|", leer_m2(anuncio), "|", barrio, "|", "https://www.pisos.com" + enlace)
