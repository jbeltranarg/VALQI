# Prueba de viabilidad — Persona B (pisos.com y habitaclia.com)

Fecha de las pruebas: 20/10/2026. Peticiones con `requests`, User-Agent propio
(`AlquilerVLC-UPV-ATD/0.1`) y pausas de 3 s.
**Nota portafolio:** pruebas y redacción hechas con ayuda de IA (Claude).

## pisos.com

1. **robots.txt:** `User-Agent: *` solo prohíbe `/busqueda/$`, `/*.aspx`, `/WS/`, `/mapa/`,
   `/alquiler-temporada/`, idiomas (`/ca/`, `/en/`...) y algunas rutas internas.
   Las páginas de listado `/alquiler/...` están permitidas.
2. **Código de estado:** 200.
3. **Contenido:** el HTML trae los anuncios (32 por página), sin CAPTCHA. No hace falta Selenium.
4. **Campos:** precio (`.ad-preview__price`), título/calle (`a.ad-preview__title`, con la URL
   del anuncio en `href`), barrio y distrito (`.ad-preview__subtitle`, p. ej.
   "Torrefiel (Distrito Rascanya. València Capital)"), y en `p.ad-preview__char`:
   habitaciones, baños, m² y planta. Trae también la descripción y un bloque JSON-LD.
5. **Paginación:** se añade el número de página como carpeta:
   `/alquiler/pisos-valencia_capital_zona_urbana/2/`.
6. **Filtro Valencia capital:** `/alquiler/pisos-valencia_capital/` (redirige a
   `/alquiler/pisos-valencia_capital_zona_urbana/`). La ciudad va en la URL y se puede parametrizar.
7. **Veredicto: VIABLE con requests + BeautifulSoup.** Ojo: incluye pedanías (El Perellonet,
   El Palmar...), que habrá que tratar al normalizar los barrios.

## habitaclia.com

1. **robots.txt:** `User-agent: *` prohíbe rutas internas (ajax, teléfono, captcha) y parámetros
   de URL (`?pag=`, `ordenar=`, `geo=`, `f=`...). Las rutas de listado sin esos parámetros
   están permitidas.
2. **Código de estado:** 200.
3. **Contenido:** el HTML trae los anuncios (29 `<article>` por página), sin CAPTCHA. No hace
   falta Selenium. El título indica 2.303 viviendas en alquiler en Valencia capital.
4. **Campos:** precio ("2.000 €/mes"), tipo y calle, barrio ("Patraix, Valencia Capital"), m²,
   habitaciones, baños, planta y la URL del anuncio. El HTML usa clases CSS genéricas de
   Tailwind, así que es más frágil de parsear que pisos.com.
5. **Paginación:** `/s/2`, `/s/3`... al final de la ruta. **No** usar el parámetro `?pag=`,
   que está prohibido en robots.txt.
6. **Filtro Valencia capital:** `/alquiler/viviendas/valencia-provincia/valencia-capital/s`.
   También hay rutas por distrito y barrio
   (`.../valencia-capital/l-eixample/russafa/s`).
7. **Veredicto: VIABLE con requests + BeautifulSoup**, con selectores más difíciles que pisos.com.

## Pendiente

- Leer el aviso legal / las condiciones de uso de ambos portales (habitaclia es del grupo
  Adevinta, igual que fotocasa y milanuncios) y citarlos en el documento.

## Comprobación rápida de los portales del resto del grupo (misma fecha)

| Portal | HTTP | Observación | Veredicto |
|---|---|---|---|
| fotocasa.es | 200 | Los anuncios están en el HTML y robots.txt no bloquea `/es/alquiler/viviendas/` | Viable (falta revisar las condiciones de uso) |
| yaencontre.com | 403 | CAPTCHA de DataDome, también en robots.txt | No viable |
| milanuncios.com | 200 | robots.txt prohíbe la paginación (`?pagina=`, `?pag`) | No viable en la práctica (solo 1 página) |
| idealista.com | 403 | Bloqueado; solo por la API oficial | Solo API |
| enalquiler.com | — | robots.txt permite los listados; lo prueba A | Viable (según A) |
