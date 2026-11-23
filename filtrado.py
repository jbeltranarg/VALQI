# Archivo: filtrado.py
# Autor: Javier Beltrán Argente
# Fecha: 21/11/2026
# Qué hace: junta los anuncios de los tres portales y los homogeneiza (UD3, filtrado
#   de datos): números, tipos de vivienda, nombres de barrio, distritos, precios
#   imposibles y anuncios repetidos. Después los cruza con los barrios oficiales del
#   Ayuntamiento (población y códigos).
# Uso de IA: Claude Opus 5.5 (Anthropic) escribió este módulo a partir de las decisiones
#   del grupo. Revisado y ejecutado por Javi.
import difflib

import pandas as pd

COLUMNAS = ["portal", "id_anuncio", "tipo", "precio", "m2", "habitaciones",
            "banos", "barrio", "distrito", "url", "fecha_recogida"]

# Límites para descartar datos imposibles (errores de los anuncios)
PRECIO_MIN = 200      # € al mes. Por debajo suele ser una habitación o un error
PRECIO_MAX = 15000
M2_MIN = 10
M2_MAX = 1000

# Tipos de vivienda que aceptamos tal cual. El resto pasa a "otro"
TIPOS = ["piso", "atico", "apartamento", "estudio", "loft", "duplex", "casa", "chalet"]

# Palabras que no ayudan a distinguir barrios ("El Carme" = "Carme")
ARTICULOS = ["EL", "LA", "LES", "ELS", "L", "LOS", "LAS", "DE", "DEL", "D", "I", "Y"]

# Nombres que los portales escriben en castellano o de otra forma.
# Izquierda: como lo escriben los portales. Derecha: nombre oficial del Ayuntamiento
SINONIMOS = {
    "Ruzafa": "RUSSAFA",
    "Cabañal": "CABANYAL-CANYAMELAR",
    "Cabanyal": "CABANYAL-CANYAMELAR",
    "El Cabanyal - El Canyamelar": "CABANYAL-CANYAMELAR",
    "Canyamelar": "CABANYAL-CANYAMELAR",
    "Malvarrosa": "LA MALVA-ROSA",
    "El Carmen": "EL CARME",
    "Botánico": "EL BOTANIC",
    "Mercado": "EL MERCAT",
    "San Francisco": "SANT FRANCESC",
    "Gran Vía": "LA GRAN VIA",
    "Ciudad de las Artes y las Ciencias": "CIUTAT DE LES ARTS I DE LES CIENCIES",
    "Ciudad Universitaria": "CIUTAT UNIVERSITARIA",
    "Ciudad Jardín": "CIUTAT JARDI",
    "Ciudad Fallera": "CIUTAT FALLERA",
    "San Isidro": "SANT ISIDRE",
    "San Pablo": "SANT PAU",
    "San Antonio": "SANT ANTONI",
    "San Marcelino": "SANT MARCEL.LI",
    "San Lorenzo": "SANT LLORENS",
    "Nazaret": "NATZARET",
    "Ayora": "AIORA",
    "Peñarroja": "PENYA-ROJA",
    "Cruz Cubierta": "LA CREU COBERTA",
    "Camino Real": "CAMI REAL",
    "Camino de Vera": "CAMI DE VERA",
    "Camino Hondo": "CAMI FONDO",
    "Exposición": "EXPOSICIO",
    "Vega Baja": "LA VEGA BAIXA",
    "Isla Perdida": "L'ILLA PERDUDA",
    "La Amistad": "L'AMISTAT",
    "La Luz": "LA LLUM",
    "Fuensanta": "LA FONTSANTA",
    "Tres Cruces": "TRES FORQUES",
    "Trinidad": "TRINITAT",
    "Calvario": "EL CALVARI",
    "Huerta de Senabre": "L'HORT DE SENABRE",
    "Rayosa": "LA RAIOSA",
    "San Luis": "LA FONTETA S.LLUIS",
    "La Fonteta": "LA FONTETA S.LLUIS",
    "Cruz del Grao": "LA CREU DEL GRAU",
    "El Grao": "EL GRAU",
    "Pueblo Nuevo": "POBLE NOU",
    "Horno de Alcedo": "EL FORN D'ALCEDO",
    "Malilla": "MALILLA",
}


def clave(texto):
    # Convierte un nombre en una "clave" para poder comparar nombres escritos de
    # formas distintas: "La Malva-rosa" -> "MALVAROSA" ; "El Botànic" -> "BOTANIC"
    texto = str(texto).upper().strip()
    cambios = {"Á": "A", "À": "A", "Ä": "A", "É": "E", "È": "E", "Ë": "E",
               "Í": "I", "Ì": "I", "Ï": "I", "Ó": "O", "Ò": "O", "Ö": "O",
               "Ú": "U", "Ù": "U", "Ü": "U", "Ñ": "N", "Ç": "C",
               "·": "", ".": "", "'": " ", "’": " ", "-": " ", "_": " "}
    for viejo, nuevo in cambios.items():
        texto = texto.replace(viejo, nuevo)
    palabras = []
    for palabra in texto.split():
        if palabra not in ARTICULOS:
            palabras.append(palabra)
    return "".join(palabras)


def buscar_nombre(texto, claves_oficiales, sinonimos):
    # Devuelve la clave oficial que corresponde a 'texto', o "" si no la encuentra.
    # 1) igual  2) diccionario de sinónimos  3) el más parecido con difflib (UD3)
    if texto is None or str(texto).strip() == "" or str(texto) == "nan":
        return ""
    k = clave(texto)
    if k in claves_oficiales:
        return k
    if k in sinonimos:
        return sinonimos[k]
    parecidos = difflib.get_close_matches(k, claves_oficiales, n=1, cutoff=0.8)
    if len(parecidos) > 0:
        return parecidos[0]
    return ""


def sinonimos_en_clave():
    # El diccionario SINONIMOS pasado a claves, para poder compararlo con clave(texto).
    # Lo usan el filtrado y el buscador de main.py, así los dos entienden los mismos nombres
    sinonimos = {}
    for escrito, oficial in SINONIMOS.items():
        sinonimos[clave(escrito)] = clave(oficial)
    return sinonimos


def normalizar_tipo(tipo):
    t = clave(tipo).lower()
    if t in TIPOS:
        return t
    return "otro"


def homogeneizar(anuncios, barrios):
    # anuncios: lista de diccionarios con las 11 columnas (de los tres portales)
    # barrios: lista de diccionarios del Ayuntamiento (scrapers/ayuntamiento.py)
    # Devuelve (tabla limpia, informe con lo que ha hecho cada paso)
    informe = []
    df = pd.DataFrame(anuncios, columns=COLUMNAS)
    informe.append(("Anuncios descargados", len(df)))

    # 1. Números: precio, m², habitaciones y baños pasan a número ("" -> vacío)
    for columna in ["precio", "m2", "habitaciones", "banos"]:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    df["fecha_recogida"] = pd.to_datetime(df["fecha_recogida"], format="%d/%m/%Y", errors="coerce")

    # 2. Repetidos dentro del mismo portal (el mismo anuncio en dos páginas)
    antes = len(df)
    df = df.drop_duplicates(subset=["portal", "id_anuncio"])
    informe.append(("Repetidos en el mismo portal (eliminados)", antes - len(df)))

    # 3. Precios imposibles o sin precio
    antes = len(df)
    df = df[(df["precio"] >= PRECIO_MIN) & (df["precio"] <= PRECIO_MAX)]
    informe.append((f"Sin precio o fuera de {PRECIO_MIN}-{PRECIO_MAX} € (eliminados)", antes - len(df)))

    # 4. Superficies imposibles: no se elimina el anuncio, solo se vacía el dato
    malos = (df["m2"] < M2_MIN) | (df["m2"] > M2_MAX)
    df.loc[malos, "m2"] = None
    informe.append((f"m² fuera de {M2_MIN}-{M2_MAX} (dato vaciado)", int(malos.sum())))

    # 5. Tipo de vivienda: misma escritura en todos los portales ("Ático" -> "atico")
    df["tipo"] = df["tipo"].apply(normalizar_tipo)

    # 6. Barrio y distrito oficiales
    tabla_barrios = pd.DataFrame(barrios)
    tabla_barrios["clave"] = tabla_barrios["barrio"].apply(clave)
    claves_barrios = list(tabla_barrios["clave"])
    claves_distritos = list(tabla_barrios["distrito"].apply(clave).unique())
    sinonimos = sinonimos_en_clave()

    claves_encontradas = []
    for _, fila in df.iterrows():
        k = buscar_nombre(fila["barrio"], claves_barrios, sinonimos)
        claves_encontradas.append(k)
    df["clave"] = claves_encontradas
    informe.append(("Barrio identificado con el nombre oficial",
                    int((df["clave"] != "").sum())))

    # Unimos con la tabla del Ayuntamiento: barrio, distrito, códigos y población oficiales
    columnas_oficiales = tabla_barrios[["clave", "barrio", "distrito", "codigo_barrio", "poblacion"]]
    columnas_oficiales = columnas_oficiales.drop_duplicates(subset=["clave"])
    columnas_oficiales = columnas_oficiales.rename(columns={
        "barrio": "barrio_oficial", "distrito": "distrito_oficial"})
    df = df.merge(columnas_oficiales, on="clave", how="left")

    # Si no hemos reconocido el barrio, al menos intentamos sacar el distrito
    # (p. ej. "Campanar, Valencia" o el distrito que da el portal)
    nombres_distritos = {}
    for d in tabla_barrios["distrito"].unique():
        nombres_distritos[clave(d)] = d
    sin_distrito = df["distrito_oficial"].isna()
    for i in df[sin_distrito].index:
        for texto in [df.at[i, "distrito"], df.at[i, "barrio"]]:
            k = buscar_nombre(texto, claves_distritos, {})
            if k != "":
                df.at[i, "distrito_oficial"] = nombres_distritos[k]
                break
    informe.append(("Distrito oficial identificado", int(df["distrito_oficial"].notna().sum())))

    # 7. El mismo piso anunciado en dos portales: mismo barrio, precio, m² y habitaciones
    antes = len(df)
    con_datos = df["barrio_oficial"].notna() & df["m2"].notna()
    repetidos = con_datos & df.duplicated(
        subset=["barrio_oficial", "precio", "m2", "habitaciones"], keep="first")
    df = df[~repetidos]
    informe.append(("Mismo piso en varios portales (eliminados)", antes - len(df)))

    # 8. Columna nueva: precio por metro cuadrado
    df["precio_m2"] = (df["precio"] / df["m2"]).round(2)

    df = df.drop(columns=["clave"])
    informe.append(("Anuncios finales", len(df)))
    return df.reset_index(drop=True), informe
