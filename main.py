# Archivo: main.py
# Autor: Javier Beltrán Argente
# Fecha: 21/11/2026
# Qué hace: programa principal de VALQI. Muestra un menú, pregunta al usuario qué
#   portales y cuántas páginas quiere descargar, llama a los módulos de scraping
#   (scrapers/), a la API del Ayuntamiento y al filtrado (filtrado.py), guarda el
#   resultado en data/ y permite consultarlo (resumen, búsqueda, comparación).
# Uso: desde la carpeta del repositorio, python main.py
# Uso de IA: Claude Opus 5.5 (Anthropic) escribió este módulo a partir de las decisiones
#   del grupo. Revisado y ejecutado por Javi.
import os

import pandas as pd

import filtrado
from scrapers import ayuntamiento, enalquiler, habitaclia, pisos

CARPETA_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_ANUNCIOS = os.path.join(CARPETA_DATOS, "valqi_anuncios.csv")
CSV_BARRIOS = os.path.join(CARPETA_DATOS, "valqi_barrios.csv")

# Portales disponibles: número del menú -> (nombre, módulo)
PORTALES = {
    "1": ("enalquiler", enalquiler),
    "2": ("pisos.com", pisos),
    "3": ("habitaclia", habitaclia),
}
MAX_PAGINAS = 10  # límite para no hacer demasiadas peticiones seguidas


def pedir_numero(pregunta, minimo, maximo, por_defecto):
    # Pide un número al usuario hasta que escriba uno válido (Enter = valor por defecto)
    while True:
        texto = input(f"{pregunta} [{minimo}-{maximo}, Enter = {por_defecto}]: ").strip()
        if texto == "":
            return por_defecto
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        print("  Valor no válido, prueba otra vez.")


def descargar():
    # Opción 1 del menú: scraping + API + filtrado
    print("\nPortales: 1 = enalquiler, 2 = pisos.com, 3 = habitaclia")
    eleccion = input("¿Cuáles quieres? (p. ej. 1,3 ; Enter = todos): ").strip()
    if eleccion == "":
        elegidos = list(PORTALES.keys())
    else:
        elegidos = []
        for parte in eleccion.split(","):
            if parte.strip() in PORTALES:
                elegidos.append(parte.strip())
    if len(elegidos) == 0:
        print("  No has elegido ningún portal válido.")
        return None, None
    paginas = pedir_numero("¿Cuántas páginas por portal?", 1, MAX_PAGINAS, 2)

    print("\n[1/3] Barrios oficiales (API del Ayuntamiento)...")
    barrios = ayuntamiento.obtener_barrios()
    if len(barrios) == 0:
        print("  No se han podido descargar los barrios. No sigo.")
        return None, None
    print(f"  {len(barrios)} barrios")

    print("[2/3] Anuncios (web scraping)...")
    anuncios = []
    for numero in elegidos:
        nombre, modulo = PORTALES[numero]
        try:
            anuncios = anuncios + modulo.obtener_anuncios(paginas)
        except Exception as error:
            # Si un portal falla (cambia su web, no responde...), seguimos con los demás
            print(f"  [{nombre}] error: {error}. Sigo con el resto.")
    if len(anuncios) == 0:
        print("  No se ha descargado ningún anuncio.")
        return None, None

    print("[3/3] Filtrado y unión de los datos...")
    tabla, informe = filtrado.homogeneizar(anuncios, barrios)
    for paso, cantidad in informe:
        print(f"  {paso}: {cantidad}")

    os.makedirs(CARPETA_DATOS, exist_ok=True)
    tabla.to_csv(CSV_ANUNCIOS, sep=";", index=False, encoding="utf-8-sig")
    pd.DataFrame(barrios).to_csv(CSV_BARRIOS, sep=";", index=False, encoding="utf-8-sig")
    print(f"  Guardado en {CSV_ANUNCIOS}")
    return tabla, pd.DataFrame(barrios)


def cargar():
    # Opción 2 del menú: usar los datos de la última descarga sin volver a descargar
    if not os.path.exists(CSV_ANUNCIOS):
        print("  Todavía no hay datos guardados: usa primero la opción 1.")
        return None, None
    tabla = pd.read_csv(CSV_ANUNCIOS, sep=";", encoding="utf-8-sig")
    barrios = pd.read_csv(CSV_BARRIOS, sep=";", encoding="utf-8-sig")
    print(f"  Cargados {len(tabla)} anuncios de {CSV_ANUNCIOS}")
    return tabla, barrios


def resumen_distritos(tabla):
    # Opción 3: precio medio y €/m² por distrito, de más caro a más barato
    resumen = tabla.groupby("distrito_oficial").agg(
        anuncios=("precio", "count"),
        precio_medio=("precio", "mean"),
        precio_m2_medio=("precio_m2", "mean"),
    ).round(0).sort_values("precio_m2_medio", ascending=False)
    print("\nPrecio del alquiler por distrito (de más caro a más barato por m²):")
    print(resumen.to_string())


def resumen_barrios(tabla, barrios):
    # Opción 4: por barrio, con la población del Ayuntamiento
    resumen = tabla.groupby(["distrito_oficial", "barrio_oficial"]).agg(
        anuncios=("precio", "count"),
        precio_medio=("precio", "mean"),
        precio_m2_medio=("precio_m2", "mean"),
        poblacion=("poblacion", "first"),
    ).round(0)
    resumen["poblacion"] = resumen["poblacion"].astype("Int64")  # 3013.0 -> 3013
    # Anuncios por cada 1.000 habitantes: cuánta oferta hay para el tamaño del barrio
    resumen["anuncios_por_1000_hab"] = (resumen["anuncios"] / resumen["poblacion"] * 1000).round(2)
    resumen = resumen.sort_values("precio_m2_medio", ascending=False)
    print(f"\nBarrios con anuncios: {len(resumen)} de {len(barrios)}")
    print(resumen.to_string())


def buscar(tabla, barrios):
    # Opción 5: el usuario filtra por barrio o distrito, precio máximo y habitaciones
    texto = input("Barrio o distrito (Enter = cualquiera): ").strip()
    precio_max = pedir_numero("Precio máximo (€/mes)", 200, 15000, 15000)
    habitaciones = pedir_numero("Habitaciones mínimas", 0, 10, 0)

    resultado = tabla
    if texto != "":
        # Reconocemos el nombre igual que en el filtrado: nombre oficial, sinónimos en
        # castellano ("Ruzafa") o el más parecido con difflib (erratas)
        claves_barrios = list(barrios["barrio"].apply(filtrado.clave))
        k = filtrado.buscar_nombre(texto, claves_barrios, filtrado.sinonimos_en_clave())
        columna = "barrio_oficial"
        tipo_zona = "barrio"
        if k == "":
            # Si no es un barrio, probamos con los distritos
            claves_distritos = list(barrios["distrito"].dropna().apply(filtrado.clave).unique())
            k = filtrado.buscar_nombre(texto, claves_distritos, {})
            columna = "distrito_oficial"
            tipo_zona = "distrito"
        if k == "":
            print(f"  No hay ningún barrio ni distrito de Valencia llamado '{texto}'.")
            return

        en_la_zona = tabla[tabla[columna].fillna("").apply(filtrado.clave) == k]
        if columna == "barrio_oficial":
            nombre = barrios[barrios["barrio"].apply(filtrado.clave) == k]["barrio"].iloc[0]
        else:
            nombre = barrios[barrios["distrito"].fillna("").apply(filtrado.clave) == k]["distrito"].iloc[0]
        print(f"  Buscando en el {tipo_zona} {nombre}")
        if len(en_la_zona) == 0:
            print(f"  El {tipo_zona} existe, pero en esta descarga no hay anuncios en él.")
            return
        resultado = en_la_zona

    resultado = resultado[resultado["precio"] <= precio_max]
    if habitaciones > 0:
        resultado = resultado[resultado["habitaciones"] >= habitaciones]

    print(f"\n{len(resultado)} anuncios encontrados. Los 10 más baratos:")
    columnas = ["portal", "tipo", "precio", "m2", "habitaciones", "barrio_oficial", "url"]
    mostrar = resultado.sort_values("precio")[columnas].head(10).copy()
    # Al haber datos vacíos, pandas guarda estos números con decimales (3.0): los pasamos
    # a enteros solo para mostrarlos (Int64 admite vacíos)
    for columna in ["precio", "m2", "habitaciones"]:
        mostrar[columna] = mostrar[columna].round(0).astype("Int64")
    print(mostrar.to_string(index=False))


def comparar_portales(tabla):
    # Opción 6: qué aporta cada portal y cómo de completos son sus datos
    resumen = tabla.groupby("portal").agg(
        anuncios=("precio", "count"),
        precio_medio=("precio", "mean"),
        precio_m2_medio=("precio_m2", "mean"),
        con_barrio=("barrio_oficial", "count"),
        con_m2=("m2", "count"),
    ).round(0)
    print("\nComparación de portales:")
    print(resumen.to_string())


def menu():
    tabla = None
    barrios = None
    while True:
        print("\n========== VALQI: alquileres en Valencia ==========")
        print("1. Descargar datos nuevos (portales + Ayuntamiento)")
        print("2. Cargar los datos de la última descarga")
        print("3. Resumen por distrito")
        print("4. Resumen por barrio (con población)")
        print("5. Buscar pisos (barrio, precio, habitaciones)")
        print("6. Comparar portales")
        print("0. Salir")
        opcion = input("Elige una opción: ").strip()

        if opcion == "0":
            print("¡Hasta luego!")
            break
        elif opcion == "1":
            tabla, barrios = descargar()
        elif opcion == "2":
            tabla, barrios = cargar()
        elif opcion in ["3", "4", "5", "6"]:
            if tabla is None:
                print("  Primero descarga (1) o carga (2) los datos.")
            elif opcion == "3":
                resumen_distritos(tabla)
            elif opcion == "4":
                resumen_barrios(tabla, barrios)
            elif opcion == "5":
                buscar(tabla, barrios)
            else:
                comparar_portales(tabla)
        else:
            print("  Opción no válida.")


if __name__ == "__main__":
    menu()
