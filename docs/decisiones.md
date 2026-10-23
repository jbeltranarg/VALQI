# Registro de decisiones del proyecto VALQI

Documento común del grupo. Recoge qué hemos decidido y por qué. Se actualiza cada vez que se toma una decisión nueva.

## 1. Portales

| Portal | Veredicto | Motivo | Decisión |
| --- | --- | --- | --- |
| Enalquiler | Viable | robots.txt permite listados y paginación; 200; anuncios en el HTML | **Se usa** (A) |
| pisos.com | Viable | robots.txt permite listados y paginación; 200; anuncios en el HTML | **Se usa** (B) |
| habitaclia | Viable | robots.txt permite la paginación por ruta (/s/N; prohíbe ?pag=); 200; anuncios en el HTML | **Se usa** (D) |
| fotocasa | Viable con limitaciones | robots.txt prohíbe la paginación: solo se puede leer la página 1 (~30 anuncios). Leer la página 1 de cada distrito sería una forma de esquivar esa norma | Descartado (23/10) |
| yaencontre | No viable | 403 y CAPTCHA (DataDome) incluso en el robots.txt | Descartado |
| milanuncios | No viable | robots.txt prohíbe la paginación y los filtros del buscador; filtra por radio, no por municipio | Descartado |
| Idealista | Solo por API | La web devuelve 403. API oficial solicitada (límite gratuito muy bajo) | Extra opcional si llega la clave (C) |

Ninguna fuente se usa con Selenium: los tres portales elegidos sirven los anuncios en el HTML.

## 2. Política de datos

Motivo: los avisos legales de los portales no prohíben expresamente el scraping, pero sí reproducir, redistribuir y explotar comercialmente sus contenidos.

- Respetamos el robots.txt de cada portal (revisado a mano: urllib.robotparser no entiende los comodines `*`).
- Nos identificamos con el User-Agent `VALQI-UPV/1.0 (proyecto universitario)` y hacemos pausas entre peticiones.
- Solo recogemos datos numéricos y de ubicación: nunca textos de anuncios, fotos ni datos del anunciante.
- Solo publicamos estadísticas agregadas (medias por barrio, €/m²), nunca anuncios individuales.
- Los datos descargados van en `data/`, que está en el .gitignore. Nunca se suben al repositorio.
- Las claves de API van en un archivo `.env`, también ignorado.
- Consulta al profesor sobre estos puntos: enviada el 23/10 (A). Pendiente de respuesta.

## 3. Alcance

- Solo alquiler, solo Valencia capital (incluidas las pedanías). La ciudad y el tipo de vivienda serán parámetros del código, para poder ampliar más adelante.
- Se recogen todos los tipos de vivienda (pisos, áticos, casas...) y el tipo se guarda como columna.

## 4. Columnas comunes

Todos los scrapers devuelven exactamente estas columnas:

| Columna | Descripción |
| --- | --- |
| portal | enalquiler / pisos / habitaclia |
| id_anuncio | Identificador del anuncio en su portal |
| tipo | piso, ático, casa, estudio... |
| precio | €/mes, número |
| m2 | Superficie, número |
| habitaciones | Número (vacío si no se indica) |
| banos | Número (vacío si no se indica) |
| barrio | Nombre tal como lo da el portal |
| distrito | Nombre tal como lo da el portal |
| url | Enlace al anuncio |
| fecha_recogida | Fecha de la descarga (dd/mm/aaaa) |

La unificación de nombres de barrio con el listado oficial se hará en la limpieza, no en el scraper.

## 5. Problemas de limpieza identificados

- **Nombres de barrio:** cada portal los escribe distinto. Se unificarán con el listado oficial del Ayuntamiento (D).
- **Duplicados entre portales:** el mismo piso puede aparecer en varios portales (C).
- **Datos irregulares:** algunos anuncios no indican habitaciones o baños; cada dato se reconoce por su texto, no por su posición.
- **Pedanías:** forman parte del municipio y se tratan como una zona más.

## 6. Reparto

| Persona | Responsabilidad |
| --- | --- |
| A (Javi) | Scraper de Enalquiler. Coordinación y consulta al profesor |
| B (Nico) | Scraper de pisos.com |
| C | Redacción del Proyecto II. Duplicados entre portales. API de Idealista si llega |
| D (Dani) | Scraper de habitaclia. Listado oficial de barrios y unificación de nombres |

## 7. Normas de trabajo

- Cada tarea en su rama (LETRA-tarea) y con Pull Request, avisando en el grupo al hacer merge.
- Cabecera estándar en cada .py, con autor, fecha y uso concreto de IA.
- Solo herramientas vistas en clase salvo acuerdo del grupo. Cada uno debe saber explicar cada línea de su código.
