# Prueba de viabilidad de Enalquiler (Persona A, VALQI)
# Descarga la página de pisos en alquiler de Valencia capital y extrae los anuncios.

import requests                    # peticiones HTTP
from bs4 import BeautifulSoup      # buscar dentro del HTML

# Página 1 de pisos en alquiler en Valencia capital
# (48 = provincia de Valencia, 2 = pisos, 50692 = municipio de Valencia)
url = "https://www.enalquiler.com/alquiler-pisos-valencia-48-2-0-50692.html"

# Nos identificamos ante la web, como acordamos en las normas del grupo
cabeceras = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}

respuesta = requests.get(url, headers=cabeceras)

# --- Comprobaciones de la ficha de viabilidad ---
print(respuesta.status_code)  # Punto 2: 200 = no nos bloquea
# print(len(respuesta.text))  # Punto 3: ~267.000 caracteres, no es una página de bloqueo
# print(respuesta.text.count("alquiler_piso_valencia/"))  # Punto 3: 15 enlaces = 15 anuncios en el HTML

# Convertimos el HTML en un árbol en el que se puede buscar por etiquetas y clases
soup = BeautifulSoup(respuesta.text, "html.parser")
# print(soup.title.text)  # Comprobación: BeautifulSoup lee bien la página

# Los datos de cada anuncio (precio, detalles, ubicación) van dentro de este div
tarjetas = soup.find_all("div", class_="propertyCard__infoWrapper")
print(len(tarjetas))  # Debería coincidir con los 15 anuncios por página

# Probamos con el primer anuncio antes de recorrerlos todos
'''
primera = tarjetas[0]
precio = primera.find("span", class_="propertyCard__price--value")
print(precio.text.strip())  # .strip() quita los espacios y saltos de línea del principio y del final.

detalles = primera.find("ul", class_="propertyCard__details")
# print(detalles.get_text(" | ", strip=True))    # get_text(" | ", strip=True) limpia cada trozo y los une con " | " entre medias.
for li in detalles.find_all("li"):
    print(li.get_text(strip=True))      #esta version del print con el bucle hace que metros quede unido a 2, (metros cuadrados), como tenia qu salir

ubicacion = primera.find("div", class_ = "propertyCard__location")
print(ubicacion.text.strip())

'''
# Recorremos los 5 primeros anuncios
for tarjeta in tarjetas[:5]:
    precio = tarjeta.find("span", class_="propertyCard__price--value").text.strip()
    detalles = tarjeta.find("ul", class_="propertyCard__details")
    datos = [li.get_text(strip=True) for li in detalles.find_all("li")]
    ubicacion = tarjeta.find("div", class_="propertyCard__location").text.strip()
    print(precio, "|", " · ".join(datos), "|", ubicacion)