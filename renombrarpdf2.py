# Felipe Jilberto 2026

import os
import re
import subprocess
import requests
from pypdf import PdfReader

# ==================================
# CONFIGURACIÓN
# ==================================

DRY_RUN = False         # True = sólo muestra cambios
DESBLOQUEAR = True      # Elimina advertencias de Windows
MAX_TITLE_LENGTH = 80

# ==================================
# UTILIDADES
# ==================================

def limpiar_nombre(texto):
    texto = re.sub(r'[\\/:*?"<>|]', '', texto)
    texto = texto.replace("\n", " ")
    texto = texto.replace("\r", " ")
    texto = re.sub(r'\s+', '_', texto)
    texto = re.sub(r'_+', '_', texto)
    return texto.strip("_")


def obtener_texto(reader, paginas=3):
    texto = ""

    for i in range(min(paginas, len(reader.pages))):
        try:
            pagina = reader.pages[i].extract_text()
            if pagina:
                texto += pagina + "\n"
        except:
            pass

    return texto


# ==================================
# DESBLOQUEAR PDF
# ==================================

def desbloquear_archivo(ruta):

    try:

        subprocess.run(
            [
                "powershell",
                "-Command",
                f'Unblock-File -Path "{ruta}"'
            ],
            capture_output=True,
            text=True
        )

    except Exception:
        pass


# ==================================
# DOI
# ==================================

def buscar_doi(texto):

    patron = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'

    encontrados = re.findall(
        patron,
        texto,
        flags=re.IGNORECASE
    )

    if encontrados:
        return encontrados[0].rstrip(".,;)")

    return None


# ==================================
# CROSSREF
# ==================================

def consultar_crossref(doi):

    try:

        url = f"https://api.crossref.org/works/{doi}"

        r = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "PaperRenamer/1.0"
            }
        )

        if r.status_code != 200:
            return None

        data = r.json()["message"]

        titulo = "TituloDesconocido"

        if data.get("title"):
            titulo = data["title"][0]

        autor = "AutorDesconocido"

        if data.get("author"):
            autor = data["author"][0].get(
                "family",
                autor
            )

        anio = "AñoDesconocido"

        if "published-print" in data:
            anio = str(
                data["published-print"]["date-parts"][0][0]
            )

        elif "published-online" in data:
            anio = str(
                data["published-online"]["date-parts"][0][0]
            )

        elif "created" in data:
            anio = str(
                data["created"]["date-parts"][0][0]
            )

        return {
            "autor": autor,
            "anio": anio,
            "titulo": titulo
        }

    except:
        return None


# ==================================
# METADATOS PDF
# ==================================

def extraer_metadatos(reader):

    try:

        meta = reader.metadata

        if not meta:
            return None

        titulo = meta.title if meta.title else ""
        autor = meta.author if meta.author else ""

        if not titulo:
            return None

        return {
            "autor": autor,
            "titulo": titulo
        }

    except:
        return None


# ==================================
# HEURÍSTICA
# ==================================

def heuristica(texto):

    lineas = [
        l.strip()
        for l in texto.splitlines()
        if l.strip()
    ]

    titulo = "TituloDesconocido"

    for linea in lineas[:20]:

        if len(linea.split()) < 5:
            continue

        basura = [
            "journal",
            "contents",
            "available online",
            "sciencedirect",
            "elsevier",
            "homepage",
            "volume",
            "issue"
        ]

        if any(
            b in linea.lower()
            for b in basura
        ):
            continue

        titulo = linea
        break

    anios = re.findall(
        r'\b(19\d{2}|20\d{2})\b',
        texto
    )

    anio = max(anios) if anios else "AñoDesconocido"

    return {
        "autor": "AutorDesconocido",
        "anio": anio,
        "titulo": titulo
    }


# ==================================
# NOMBRE FINAL
# ==================================

def construir_nombre(datos):

    autor = datos.get(
        "autor",
        "AutorDesconocido"
    )

    anio = datos.get(
        "anio",
        "AñoDesconocido"
    )

    titulo = datos.get(
        "titulo",
        "TituloDesconocido"
    )

    if "," in autor:
        autor = autor.split(",")[0]

    autor = autor.split(" ")[0]

    autor = limpiar_nombre(autor)

    if not autor:
        autor = "AutorDesconocido"

    titulo = limpiar_nombre(titulo)

    titulo = titulo[:MAX_TITLE_LENGTH]

    return f"{autor}_{anio}_{titulo}.pdf"


# ==================================
# PROCESAR PDF
# ==================================

def procesar_pdf(ruta_pdf):

    try:

        reader = PdfReader(ruta_pdf)

        texto = obtener_texto(reader)

        doi = buscar_doi(texto)

        if doi:

            datos = consultar_crossref(doi)

            if datos:
                return construir_nombre(datos)

        meta = extraer_metadatos(reader)

        if meta:

            anios = re.findall(
                r'\b(19\d{2}|20\d{2})\b',
                texto
            )

            meta["anio"] = (
                max(anios)
                if anios
                else "AñoDesconocido"
            )

            return construir_nombre(meta)

        datos = heuristica(texto)

        return construir_nombre(datos)

    except Exception as e:

        print(
            f"ERROR: {os.path.basename(ruta_pdf)}"
        )

        print(e)

        return None


# ==================================
# ARCHIVO YA RENOMBRADO
# ==================================

def ya_renombrado(nombre):

    patron = r'.+_\d{4}_.+\.pdf$'

    return bool(
        re.match(
            patron,
            nombre,
            flags=re.IGNORECASE
        )
    )


# ==================================
# MAIN
# ==================================

def renombrar_carpeta():

    carpeta = os.path.dirname(
        os.path.abspath(__file__)
    )

    print("\n================================")
    print(" PAPER RENAMER ")
    print("================================\n")

    for archivo in os.listdir(carpeta):

        if not archivo.lower().endswith(".pdf"):
            continue

        if ya_renombrado(archivo):
            print(
                f"[SKIP] {archivo}"
            )
            continue

        ruta_original = os.path.join(
            carpeta,
            archivo
        )

        nuevo_nombre = procesar_pdf(
            ruta_original
        )

        if not nuevo_nombre:
            continue

        ruta_nueva = os.path.join(
            carpeta,
            nuevo_nombre
        )

        contador = 1

        while os.path.exists(ruta_nueva):

            nombre, ext = os.path.splitext(
                nuevo_nombre
            )

            ruta_nueva = os.path.join(
                carpeta,
                f"{nombre}_{contador}{ext}"
            )

            contador += 1

        print(
            f"\n{archivo}"
        )

        print(
            f" -> {os.path.basename(ruta_nueva)}"
        )

        if DRY_RUN:
            continue

        os.rename(
            ruta_original,
            ruta_nueva
        )

        if DESBLOQUEAR:
            desbloquear_archivo(
                ruta_nueva
            )

        print(
            " [OK]"
        )

    print("\nProceso terminado.\n")


if __name__ == "__main__":
    renombrar_carpeta()
