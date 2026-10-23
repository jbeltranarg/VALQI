# Prueba de viabilidad de fotocasa.es: VIABLE CON LIMITACIONES FUERTES
# (ver docs/fichas/fotocasa.md). Proyecto VALQI - ATD (UPV). Persona C.
# Uso de IA: script generado con Claude (Anthropic) y explicado línea a línea.
#
# Este script NO extrae anuncios. Solo comprueba:
#   1) qué dice robots.txt (ojo: urllib.robotparser no entiende los comodines *),
#   2) qué código de estado devuelve el servidor,
#   3) si el HTML contiene los anuncios o una página de bloqueo,
#   4) cuántos anuncios distintos trae la página 1.
# Resultado de la prueba del 23/10/2026: 200, 1.519.351 caracteres, 31 anuncios.

import re
import requests
from urllib.robotparser import RobotFileParser

URL = "https://www.fotocasa.es/es/alquiler/viviendas/valencia-capital/todas-las-zonas/l"
USER_AGENT = "VALQI-UPV/1.0 (proyecto academico ATD)"
HEADERS = {"User-Agent": USER_AGENT}

# 1) Comprobar robots.txt
robots = RobotFileParser()
robots.set_url("https://www.fotocasa.es/robots.txt")
robots.read()
print("¿robots.txt permite la página 1?", robots.can_fetch(USER_AGENT, URL))
# Devuelve True, pero es un falso positivo: la regla Disallow: /*/l/2* lleva un
# comodín que robotparser no interpreta. Con la lectura estándar está prohibida.
print("¿robots.txt permite la página 2?", robots.can_fetch(USER_AGENT, URL + "/2"))

# 2) Pedir la página una sola vez
respuesta = requests.get(URL, headers=HEADERS, timeout=15)
print("Código de estado:", respuesta.status_code)
print("Tamaño del HTML:", len(respuesta.text), "caracteres")

# 3) Buscar señales de bloqueo en el HTML
html = respuesta.text.lower()
for palabra in ["captcha", "robot", "verify", "access denied"]:
    if palabra in html:
        print("Posible bloqueo: aparece la palabra", repr(palabra))
print("Hay datos JSON incrustados:",
      "__NEXT_DATA__" in respuesta.text or "INITIAL_PROPS" in respuesta.text)

# 4) Contar anuncios distintos (enlaces que terminan en /<número de anuncio>/d)
ids = set(re.findall(r"/alquiler/vivienda/[^\"'\s]*?/(\d{6,})/d", respuesta.text))
print("Anuncios distintos en la página 1:", len(ids))

# Guardar el HTML para revisarlo (no se sube al repositorio)
with open("fotocasa_p1.html", "w", encoding="utf-8") as f:
    f.write(respuesta.text)
print("HTML guardado en fotocasa_p1.html")
