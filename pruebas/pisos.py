# Archivo: pruebas/pisos.py
# Autor: Persona B (Nico)
# Fecha: 28/10/2026
# Qué hace: descarga la página 1 de alquileres de Valencia capital en pisos.com,
#   extrae las columnas comunes de cada anuncio, imprime 5 y guarda la página en CSV.
# Uso de IA: sí; se detalla en la exposición oral.
import csv
from datetime import date

import requests
from bs4 import BeautifulSoup

PORTAL = "pisos"
CIUDAD = "valencia_capital"
# pisos.com redirige esta URL a .../pisos-valencia_capital_zona_urbana/,
# que es la misma página e incluye las pedanías (Benimàmet, El Perellonet...)
URL = f"https://www.pisos.com/alquiler/pisos-{CIUDAD}/"
CABECERAS = {"User-Agent": "VALQI-UPV/1.0 (proyecto universitario)"}

COLUMNAS = ["portal", "id_anuncio", "tipo", "precio", "m2", "habitaciones",
            "banos", "barrio", "distrito", "url", "fecha_recogida"]


def numero(texto):
    # "1.100 €/mes" -> 1100 ; "161 m²" -> 161 ; "4 habs." -> 4
    # Nos quedamos con la primera palabra, quitamos los puntos de miles y la pasamos a entero
    try:
        return int(texto.split()[0].replace(".", ""))
    except ValueError:
        return ""  # p. ej. "A consultar": lo dejamos vacío, no nos lo inventamos


def leer_caracteristica(anuncio, palabra):
    # Habitaciones, baños, m² y planta comparten la misma clase y no siempre
    # aparecen todos, así que reconocemos cada dato por su texto, no por su posición
    for car in anuncio.find_all("p", class_="ad-preview__char"):
        texto = car.get_text(strip=True)
        if palabra in texto:
            return numero(texto)
    return ""


# Paso 1: descargar la página (una sola petición)
respuesta = requests.get(URL, headers=CABECERAS, timeout=20)
if respuesta.status_code != 200:
    print("Aviso: la web ha devuelto el código", respuesta.status_code)
    exit()

# Paso 2: encontrar los anuncios
sopa = BeautifulSoup(respuesta.text, "html.parser")
anuncios = sopa.find_all("div", class_="ad-preview")

# Pasos 3 y 4: sacar cada columna y dejarla en el formato común
hoy = date.today().strftime("%d/%m/%Y")
anuncios_limpios = []

for anuncio in anuncios:
    titulo = anuncio.find("a", class_="ad-preview__title")
    precio = anuncio.find(class_="ad-preview__price").get_text(strip=True)

    # El subtítulo es "Barrio (Distrito Nombre. València Capital)"
    ubicacion = anuncio.find("p", class_="ad-preview__subtitle").get_text(strip=True)
    barrio = ubicacion.split(" (")[0]
    distrito = ""
    if "Distrito " in ubicacion:
        distrito = ubicacion.split("Distrito ")[1].split(".")[0]

    anuncios_limpios.append({
        "portal": PORTAL,
        "id_anuncio": anuncio["id"],                    # atributo id del div del anuncio
        "tipo": titulo.get_text(strip=True).split()[0].lower(),  # "Ático en ..." -> "ático"
        "precio": numero(precio),
        "m2": leer_caracteristica(anuncio, "m²"),
        "habitaciones": leer_caracteristica(anuncio, "hab"),
        "banos": leer_caracteristica(anuncio, "baño"),
        "barrio": barrio,
        "distrito": distrito,
        "url": "https://www.pisos.com" + titulo.get("href"),
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
with open("data/B_pisos_muestra.csv", "w", newline="", encoding="utf-8-sig") as f:
    escritor = csv.writer(f, delimiter=";")
    escritor.writerow(COLUMNAS)
    for anuncio in anuncios_limpios:
        fila = []
        for columna in COLUMNAS:
            fila.append(anuncio[columna])
        escritor.writerow(fila)
print("CSV guardado")
