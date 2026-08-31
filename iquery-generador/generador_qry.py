#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de archivos .qry para iQuery
======================================

Reproduce exactamente la estructura del reporte "Discount Daily Total"
(subject, columnas, orden y filtro de sucursales) y solo cambia los
productos consultados (discNum).

El rango de fechas ya NO se pregunta: iQuery lo ignora y lo reemplaza por
la fecha del día, así que el periodo se ajusta dentro de iQuery al abrir
la consulta. Ver INCLUIR_FILTRO_FECHAS más abajo.

Los archivos se guardan dentro de la carpeta `codigos/`, en la subcarpeta
(campaña) que elijas en cada corrida.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

VERSION = "4.1"

# ---------------------------------------------------------------------------
# CONFIGURACIÓN (esto es lo que se queda fijo en todos los .qry)
# ---------------------------------------------------------------------------

ORGANIZACION = "BPM"
SUBJECT = "Discount Daily Total"
VERSION_PROGRAMA = "20.4.0.166"
VERSION_METADATA = "19"

COLUMNAS = [
    {"index": 0, "name": "discName"},
    {"index": 1, "name": "discNum"},
    {"index": 2, "name": "discAmt", "aggregate": "sum"},
    {"index": 3, "name": "discCnt", "aggregate": "sum"},
    {"index": 4, "name": "locName"},
]

ORDENES = [
    {"index": 0, "name": "locName", "direction": "ASC"},
]

# Sucursales (locName) incluidas en la consulta
SUCURSALES = [7208, 9792, 8937, 11141, 13145, 14275, 3648]

# El filtro de fechas se escribe con la fecha de hoy, igual que hace iQuery,
# nada más para que el archivo conserve la misma estructura que él exporta.
# Si algún día quieres generar el .qry SIN ese filtro, pon esto en False.
INCLUIR_FILTRO_FECHAS = True

# Carpeta raíz donde viven las subcarpetas por campaña
CARPETA_CODIGOS = "codigos"

# ---------------------------------------------------------------------------
# ESTILO DE LA PANTALLA
# ---------------------------------------------------------------------------

ANCHO = 64          # ancho de las líneas separadoras
SANGRIA = "  "      # margen izquierdo de todo
PROMPT = "      "   # margen de las preguntas

ESTILO = {
    "doble": "=", "simple": "-", "vertical": "|",
    "esquina_sup": "+", "esquina_inf": "+", "vineta": "-", "ok": "OK:",
}


def preparar_salida() -> None:
    """Evita que la consola de Windows tumbe el programa por los acentos.

    cmd.exe suele usar cp850/cp437, donde algunos caracteres no existen.
    Con errors="replace" se imprimen como '?' en lugar de reventar el programa.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(errors="replace")  # Python 3.7+
        except Exception:
            pass


def soporta(texto: str) -> bool:
    """¿La consola puede imprimir estos caracteres?"""
    codificacion = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        texto.encode(codificacion)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def configurar_estilo() -> None:
    """Usa caracteres de dibujo si la consola los soporta; si no, ASCII."""
    if soporta("═─│┌└·"):
        ESTILO.update(
            doble="═", simple="─", vertical="│",
            esquina_sup="┌", esquina_inf="└", vineta="·",
        )
    if soporta("✔"):
        ESTILO["ok"] = "✔"


def linea(caracter: str) -> None:
    print(SANGRIA + caracter * ANCHO)


def encabezado(titulo: str, derecha: str = "") -> None:
    linea(ESTILO["doble"])
    if derecha:
        relleno = max(ANCHO - len(titulo) - len(derecha) - 4, 1)
        print(f"{SANGRIA}  {titulo}{' ' * relleno}{derecha}")
    else:
        print(f"{SANGRIA}  {titulo}")
    linea(ESTILO["doble"])


def subtitulo(texto: str) -> None:
    print()
    linea(ESTILO["simple"])
    print(f"{SANGRIA}  {texto}")
    linea(ESTILO["simple"])


def paso(numero: int, total: int, titulo: str) -> None:
    print(f"\n{SANGRIA}[ PASO {numero} de {total} ]   {titulo}\n")


def nota(texto: str) -> None:
    print(f"{SANGRIA}  {texto}")


def resultado(texto: str) -> None:
    print(f"{PROMPT}-> {texto}")


# ---------------------------------------------------------------------------
# UTILIDADES DE ENTRADA
# ---------------------------------------------------------------------------


def leer(mensaje: str) -> str:
    """input() que sale limpio con Ctrl+C o Ctrl+D."""
    try:
        return input(mensaje).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\n  Operación cancelada. ¡Hasta luego!\n")
        sys.exit(0)


def pedir_entero(mensaje: str, minimo: int, maximo: int) -> int:
    """Pide un número. `mensaje` describe qué se debe escribir."""
    while True:
        valor = leer(PROMPT + mensaje)
        if not valor:
            resultado(f"No escribiste nada. Escribe un número del {minimo} al {maximo}.")
            continue
        if not valor.isdigit():
            resultado(f"'{valor}' no es un número. Escribe un número del {minimo} al {maximo}.")
            continue
        numero = int(valor)
        if not minimo <= numero <= maximo:
            resultado(f"Debe ser un número del {minimo} al {maximo}.")
            continue
        return numero


def pedir_si_no(pregunta: str) -> bool:
    """Pregunta de sí/no. Se contesta con 's' o 'n'."""
    while True:
        respuesta = leer(f"{PROMPT}{pregunta} (s / n): ").lower()
        if respuesta in ("s", "si", "sí", "y", "yes"):
            return True
        if respuesta in ("n", "no"):
            return False
        resultado("Escribe 's' para sí, o 'n' para no.")


# ---------------------------------------------------------------------------
# PRODUCTOS (discNum)
# ---------------------------------------------------------------------------


def pedir_discnums() -> list[str]:
    nota("Escribe el discNum de un producto y presiona Enter.")
    nota("Puedes escribir varios de una vez separados por coma o espacio (ej. 207, 206).")
    nota("Cuando ya no quieras agregar más, deja la línea vacía y presiona Enter.")
    print()

    discnums: list[str] = []
    while True:
        entrada = leer(
            f"{PROMPT}Producto #{len(discnums) + 1} (escribe el discNum): "
        )
        if not entrada:
            if discnums:
                return discnums
            resultado("Necesitas agregar al menos un producto (discNum).")
            continue

        for pieza in re.split(r"[,\s;]+", entrada):
            if not pieza:
                continue
            if not pieza.isdigit():
                resultado(f"'{pieza}' no es un número válido, se omite.")
                continue
            if pieza in discnums:
                resultado(f"El discNum {pieza} ya estaba en la lista, se omite.")
                continue
            discnums.append(pieza)

        if discnums:
            resultado(f"En la lista: {', '.join(discnums)}")


def pedir_modo(discnums: list[str]) -> str:
    """Con 2 o más productos: ¿un solo archivo con el total, o uno por producto?"""
    juntos = "-".join(discnums) + ".qry"
    sueltos = [f"{d}.qry" for d in discnums]
    separados = "  y  ".join(sueltos)
    if len(separados) > 44:
        separados = f"{sueltos[0]}, {sueltos[1]}, ...  ({len(sueltos)} archivos)"

    print()
    nota("Metiste varios productos. ¿Cómo los quieres?")
    print()
    print(f"{PROMPT}  1)  Todos juntos en un mismo archivo  (total de la campaña)")
    print(f"{PROMPT}      -> {juntos}")
    print()
    print(f"{PROMPT}  2)  Cada producto en su propio archivo  (uno por reporte)")
    print(f"{PROMPT}      -> {separados}")
    print()

    if pedir_entero("Opción (escribe 1 o 2): ", 1, 2) == 1:
        return "juntos"
    return "separados"


# ---------------------------------------------------------------------------
# CARPETAS
# ---------------------------------------------------------------------------


def limpiar_nombre(nombre: str) -> str:
    """Quita caracteres que no se pueden usar en nombres de archivo/carpeta."""
    limpio = re.sub(r'[<>:"/\\|?*]', "", nombre).strip(" .")
    return re.sub(r"\s+", " ", limpio)


def carpetas_existentes(base: Path) -> list[Path]:
    return sorted(
        (p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=lambda p: p.name.lower(),
    )


def crear_carpeta_nueva(base: Path) -> Path:
    while True:
        nombre = limpiar_nombre(
            leer(f"{PROMPT}Nombre de la nueva carpeta (ejemplo: Hora Bostons): ")
        )
        if not nombre:
            resultado("El nombre no puede quedar vacío.")
            continue
        destino = base / nombre
        if destino.exists():
            resultado(f"La carpeta '{nombre}' ya existe; se usará esa.")
        destino.mkdir(parents=True, exist_ok=True)
        resultado(f"Se guardará en: {CARPETA_CODIGOS}/{destino.name}/")
        return destino


def elegir_carpeta(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    existentes = carpetas_existentes(base)

    if not existentes:
        nota(f"Todavía no hay carpetas dentro de '{CARPETA_CODIGOS}'. Vamos a crear la primera.")
        print()
        return crear_carpeta_nueva(base)

    nota(f"Carpetas que ya existen dentro de '{CARPETA_CODIGOS}':")
    print()
    for i, carpeta in enumerate(existentes, start=1):
        cantidad = len(list(carpeta.glob("*.qry")))
        plural = "archivo" if cantidad == 1 else "archivos"
        print(f"{PROMPT}  {i})  {carpeta.name:<24}({cantidad} {plural} .qry)")
    print()

    nota("¿Qué quieres hacer?")
    print()
    print(f"{PROMPT}  1)  Guardar en una de las carpetas de arriba")
    print(f"{PROMPT}  2)  Crear una carpeta nueva")
    print()

    opcion = pedir_entero("Opción (escribe 1 o 2): ", 1, 2)
    if opcion == 2:
        return crear_carpeta_nueva(base)

    indice = pedir_entero(
        f"Carpeta (escribe el número de la carpeta, 1-{len(existentes)}): ",
        1,
        len(existentes),
    )
    elegida = existentes[indice - 1]
    resultado(f"Se guardará en: {CARPETA_CODIGOS}/{elegida.name}/")
    return elegida


# ---------------------------------------------------------------------------
# CONSTRUCCIÓN DEL .QRY
# ---------------------------------------------------------------------------


def construir_reporte(discnums: list[str]) -> dict:
    filtros_producto = [
        {
            "comparison": "EQUAL",
            "data": discnum,
            "filterName": "relationalFilter",
            "columnName": "discNum",
            "index": i,
            "logic": "OR",
        }
        for i, discnum in enumerate(discnums)
    ]

    # Filtros generales: fechas (opcional) + sucursales
    filtros_generales: list[dict] = []

    if INCLUIR_FILTRO_FECHAS:
        hoy = date.today().isoformat()
        filtros_generales.append(
            {
                "start": hoy,
                "end": hoy,
                "filterName": "dateRangeFilter",
                "columnName": "busDate",
                "index": 0,
            }
        )

    filtros_generales.append(
        {
            "filterItems": SUCURSALES,
            "filterName": "longFilter",
            "columnName": "locName",
            "index": len(filtros_generales),
        }
    )

    return {
        "subjectName": SUBJECT,
        "columns": COLUMNAS,
        "orders": ORDENES,
        "filters": [
            {"index": 0, "filters": filtros_generales},
            {"index": 100, "filters": filtros_producto},
        ],
    }


def sello_de_tiempo() -> str:
    """Mismo formato que iQuery: 8/31/2026 12:12:16 PM"""
    ahora = datetime.now()
    hora12 = ahora.hour % 12 or 12
    sufijo = "AM" if ahora.hour < 12 else "PM"
    return f"{ahora.month}/{ahora.day}/{ahora.year} {hora12}:{ahora.minute:02d}:{ahora.second:02d} {sufijo}"


def construir_qry(discnums: list[str]) -> str:
    reporte = json.dumps(
        construir_reporte(discnums),
        separators=(",", ":"),
        ensure_ascii=False,
    )
    lineas = [
        "# iQuery",
        f"# {sello_de_tiempo()}",
        f"Organization={ORGANIZACION}",
        f"subject={SUBJECT}",
        f"report={reporte}",
        f"ProgramVersion={VERSION_PROGRAMA}",
        f"MetadataVersion={VERSION_METADATA}",
    ]
    # iQuery usa saltos de línea de Windows (CRLF)
    return "\r\n".join(lineas) + "\r\n"


def nombre_archivo(discnums: list[str]) -> str:
    """Solo el número del producto, o los números unidos con guion."""
    return "-".join(discnums) + ".qry"


def guardar(contenido: str, carpeta: Path, nombre: str) -> Path:
    destino = carpeta / nombre
    if destino.exists():
        print()
        resultado(f"Ya existe el archivo '{destino.name}' en {carpeta.name}/.")
        if not pedir_si_no("¿Quieres reemplazarlo?"):
            base, extension = destino.stem, destino.suffix
            contador = 2
            while (carpeta / f"{base} ({contador}){extension}").exists():
                contador += 1
            destino = carpeta / f"{base} ({contador}){extension}"
            resultado(f"Se guardará como '{destino.name}'.")

    # newline="" evita que Python vuelva a traducir los CRLF
    with open(destino, "w", encoding="utf-8", newline="") as archivo:
        archivo.write(contenido)
    return destino


def mostrar_resumen_archivos(creados: list[tuple[Path, list[str]]]) -> None:
    vertical = ESTILO["vertical"]
    vineta = ESTILO["vineta"]
    carpeta = creados[0][0].parent

    print()
    if len(creados) == 1:
        destino, discnums = creados[0]
        print(f"{SANGRIA}{ESTILO['esquina_sup']}{ESTILO['simple']} {ESTILO['ok']} ARCHIVO GENERADO")
        print(f"{SANGRIA}{vertical}")
        print(f"{SANGRIA}{vertical}   Archivo    :  {destino.name}")
        print(f"{SANGRIA}{vertical}   Carpeta    :  {CARPETA_CODIGOS}/{carpeta.name}")
        print(f"{SANGRIA}{vertical}   Productos  :  {', '.join(discnums)}")
    else:
        print(
            f"{SANGRIA}{ESTILO['esquina_sup']}{ESTILO['simple']} {ESTILO['ok']} "
            f"{len(creados)} ARCHIVOS GENERADOS"
        )
        print(f"{SANGRIA}{vertical}")
        print(f"{SANGRIA}{vertical}   Carpeta    :  {CARPETA_CODIGOS}/{carpeta.name}")
        print(f"{SANGRIA}{vertical}")
        for destino, discnums in creados:
            etiqueta = "producto" if len(discnums) == 1 else "productos"
            print(
                f"{SANGRIA}{vertical}   {vineta} {destino.name:<28}"
                f"({etiqueta} {', '.join(discnums)})"
            )
    print(f"{SANGRIA}{vertical}")
    print(f"{SANGRIA}{ESTILO['esquina_inf']}{ESTILO['simple'] * (ANCHO - 1)}")


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------


def main() -> None:
    preparar_salida()
    configurar_estilo()

    base = Path(__file__).resolve().parent / CARPETA_CODIGOS

    print()
    encabezado("GENERADOR DE CONSULTAS .qry PARA iQuery", f"v{VERSION}")
    print()
    nota(f"Reporte     :  {SUBJECT}")
    nota(f"Se guarda en:  {base}")
    print()
    nota("El rango de fechas se ajusta dentro de iQuery, al abrir la consulta.")

    discnums: list[str] = []
    carpeta = None
    generados: list[Path] = []
    numero_consulta = 0

    while True:
        numero_consulta += 1
        subtitulo(f"CONSULTA #{numero_consulta}")

        # --- Paso 1: productos ---
        paso(1, 2, "PRODUCTOS (discNum)")
        if discnums:
            nota(f"Consulta anterior:  {', '.join(discnums)}")
            print()
            if not pedir_si_no("¿Quieres usar esos mismos productos?"):
                print()
                discnums = pedir_discnums()
        else:
            discnums = pedir_discnums()

        modo = pedir_modo(discnums) if len(discnums) > 1 else "juntos"

        # --- Paso 2: carpeta ---
        paso(2, 2, "DÓNDE GUARDAR EL ARCHIVO")
        if carpeta:
            nota(f"Consulta anterior:  {CARPETA_CODIGOS}/{carpeta.name}/")
            print()
            if not pedir_si_no("¿Quieres guardarlo en esa misma carpeta?"):
                print()
                carpeta = elegir_carpeta(base)
        else:
            carpeta = elegir_carpeta(base)

        # --- Generar (un archivo con todo, o uno por producto) ---
        grupos = [discnums] if modo == "juntos" else [[d] for d in discnums]

        creados: list[tuple[Path, list[str]]] = []
        for grupo in grupos:
            contenido = construir_qry(grupo)
            destino = guardar(contenido, carpeta, nombre_archivo(grupo))
            generados.append(destino)
            creados.append((destino, grupo))

        mostrar_resumen_archivos(creados)

        print()
        if not pedir_si_no("¿Quieres hacer otra consulta?"):
            break

    total = len(generados)
    plural = "archivo generado" if total == 1 else "archivos generados"
    print()
    encabezado(f"LISTO   {ESTILO['vineta']}   {total} {plural}")
    print()
    for archivo in generados:
        nota(f"{ESTILO['vineta']} {archivo.parent.name}/{archivo.name}")
    print()
    nota("Los archivos están en:")
    nota(f"  {base}")
    print()
    nota("Recuerda ajustar el rango de fechas dentro de iQuery al abrir cada consulta.")
    print()
    nota("¡Hasta luego!")
    print()


if __name__ == "__main__":
    main()
