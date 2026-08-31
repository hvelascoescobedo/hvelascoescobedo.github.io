#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de archivos .qry para iQuery
======================================

Reproduce exactamente la estructura del reporte "Discount Daily Total"
(subject, columnas, orden y filtro de sucursales) y solo cambia:

  * el rango de fechas (busDate)
  * los productos consultados (discNum)

Los archivos se guardan dentro de la carpeta `codigos/`, en la subcarpeta
(campaña) que elijas en cada corrida.
"""

from __future__ import annotations

import calendar
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

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

# Carpeta raíz donde viven las subcarpetas por campaña
CARPETA_CODIGOS = "codigos"

# Formato del nombre del archivo: "DiscNums FechaInicio - FechaFin.qry"
FORMATO_FECHA_ARCHIVO = "%d-%m-%Y"
SEPARADOR_FECHAS = " - "

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

# ---------------------------------------------------------------------------
# UTILIDADES DE ENTRADA
# ---------------------------------------------------------------------------


def leer(mensaje: str) -> str:
    """input() que sale limpio con Ctrl+C o Ctrl+D."""
    try:
        return input(mensaje).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\nOperación cancelada. ¡Hasta luego!")
        sys.exit(0)


def pedir_entero(mensaje: str, minimo: int, maximo: int) -> int:
    while True:
        valor = leer(mensaje)
        if not valor.isdigit():
            print(f"  -> Escribe un número entre {minimo} y {maximo}.")
            continue
        numero = int(valor)
        if not minimo <= numero <= maximo:
            print(f"  -> Debe estar entre {minimo} y {maximo}.")
            continue
        return numero


def pedir_si_no(mensaje: str, por_defecto: bool = True) -> bool:
    sufijo = " [S/n]: " if por_defecto else " [s/N]: "
    while True:
        respuesta = leer(mensaje + sufijo).lower()
        if not respuesta:
            return por_defecto
        if respuesta in ("s", "si", "sí", "y", "yes"):
            return True
        if respuesta in ("n", "no"):
            return False
        print("  -> Responde 's' o 'n'.")


# ---------------------------------------------------------------------------
# FECHAS
# ---------------------------------------------------------------------------


def pedir_fecha(etiqueta: str) -> date:
    """Pregunta día, luego mes (1 = Enero ... 12 = Diciembre) y luego año."""
    while True:
        print(f"\n--- Fecha de {etiqueta} ---")
        dia = pedir_entero("  Día (1-31): ", 1, 31)

        print("  Mes:  1.Ene  2.Feb  3.Mar  4.Abr   5.May  6.Jun")
        print("        7.Jul  8.Ago  9.Sep 10.Oct  11.Nov 12.Dic")
        mes = pedir_entero("  Mes (1-12): ", 1, 12)

        anio = pedir_entero("  Año (ej. 2026): ", 2000, 2100)

        dias_del_mes = calendar.monthrange(anio, mes)[1]
        if dia > dias_del_mes:
            print(
                f"\n  !! {MESES[mes - 1]} de {anio} solo tiene {dias_del_mes} días. "
                "Vuelve a capturar la fecha."
            )
            continue

        fecha = date(anio, mes, dia)
        print(f"  = {fecha.day} de {MESES[mes - 1]} de {fecha.year}  ({fecha.isoformat()})")
        return fecha


def pedir_rango_fechas() -> tuple[date, date]:
    while True:
        inicio = pedir_fecha("INICIO")
        fin = pedir_fecha("FIN")
        if fin < inicio:
            print("\n  !! La fecha de fin es anterior a la de inicio. Captúralas de nuevo.")
            continue
        return inicio, fin


# ---------------------------------------------------------------------------
# PRODUCTOS (discNum)
# ---------------------------------------------------------------------------


def pedir_discnums() -> list[str]:
    print("\n--- Productos (discNum) ---")
    print("  Escribe un discNum por línea, o varios separados por coma/espacio.")
    print("  Deja la línea vacía y presiona Enter para terminar.")

    discnums: list[str] = []
    while True:
        entrada = leer(f"  discNum #{len(discnums) + 1} (Enter para terminar): ")
        if not entrada:
            if discnums:
                return discnums
            print("  -> Necesitas al menos un discNum.")
            continue

        for pieza in re.split(r"[,\s;]+", entrada):
            if not pieza:
                continue
            if not pieza.isdigit():
                print(f"  -> '{pieza}' no es un número válido, se omite.")
                continue
            if pieza in discnums:
                print(f"  -> {pieza} ya estaba en la lista, se omite.")
                continue
            discnums.append(pieza)

        if discnums:
            print(f"  Productos hasta ahora: {', '.join(discnums)}")


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
        nombre = limpiar_nombre(leer("  Nombre de la nueva carpeta (ej. Hora Bostons): "))
        if not nombre:
            print("  -> El nombre no puede quedar vacío.")
            continue
        destino = base / nombre
        if destino.exists():
            print(f"  -> '{nombre}' ya existe; se usará esa carpeta.")
        destino.mkdir(parents=True, exist_ok=True)
        return destino


def elegir_carpeta(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    print(f"\n--- ¿Dónde guardo el archivo?  ({base.name}/) ---")

    existentes = carpetas_existentes(base)
    if not existentes:
        print("  Todavía no hay carpetas dentro de 'codigos'. Vamos a crear la primera.")
        return crear_carpeta_nueva(base)

    print("  1. Guardar en una carpeta ya existente")
    print("  2. Crear una carpeta nueva")
    opcion = pedir_entero("  Opción (1-2): ", 1, 2)

    if opcion == 2:
        return crear_carpeta_nueva(base)

    print(f"\n  {base.name} ->")
    for i, carpeta in enumerate(existentes, start=1):
        cantidad = len(list(carpeta.glob("*.qry")))
        print(f"    {i}. {carpeta.name}  ({cantidad} .qry)")
    indice = pedir_entero(f"  Elige una carpeta (1-{len(existentes)}): ", 1, len(existentes))
    return existentes[indice - 1]


# ---------------------------------------------------------------------------
# CONSTRUCCIÓN DEL .QRY
# ---------------------------------------------------------------------------


def construir_reporte(inicio: date, fin: date, discnums: list[str]) -> dict:
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

    return {
        "subjectName": SUBJECT,
        "columns": COLUMNAS,
        "orders": ORDENES,
        "filters": [
            {
                "index": 0,
                "filters": [
                    {
                        "start": inicio.isoformat(),
                        "end": fin.isoformat(),
                        "filterName": "dateRangeFilter",
                        "columnName": "busDate",
                        "index": 0,
                    },
                    {
                        "filterItems": SUCURSALES,
                        "filterName": "longFilter",
                        "columnName": "locName",
                        "index": 1,
                    },
                ],
            },
            {
                "index": 100,
                "filters": filtros_producto,
            },
        ],
    }


def sello_de_tiempo() -> str:
    """Mismo formato que iQuery: 8/31/2026 12:12:16 PM"""
    ahora = datetime.now()
    hora12 = ahora.hour % 12 or 12
    sufijo = "AM" if ahora.hour < 12 else "PM"
    return f"{ahora.month}/{ahora.day}/{ahora.year} {hora12}:{ahora.minute:02d}:{ahora.second:02d} {sufijo}"


def construir_qry(inicio: date, fin: date, discnums: list[str]) -> str:
    reporte = json.dumps(
        construir_reporte(inicio, fin, discnums),
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


def nombre_archivo(discnums: list[str], inicio: date, fin: date) -> str:
    productos = "-".join(discnums)
    rango = (
        inicio.strftime(FORMATO_FECHA_ARCHIVO)
        + SEPARADOR_FECHAS
        + fin.strftime(FORMATO_FECHA_ARCHIVO)
    )
    return f"{productos} {rango}.qry"


def guardar(contenido: str, carpeta: Path, nombre: str) -> Path:
    destino = carpeta / nombre
    if destino.exists():
        print(f"\n  !! Ya existe '{destino.name}' en {carpeta.name}/.")
        if not pedir_si_no("  ¿Lo sobrescribo?", por_defecto=False):
            base, extension = destino.stem, destino.suffix
            contador = 2
            while (carpeta / f"{base} ({contador}){extension}").exists():
                contador += 1
            destino = carpeta / f"{base} ({contador}){extension}"
            print(f"  -> Se guardará como '{destino.name}'.")

    # newline="" evita que Python vuelva a traducir los CRLF
    with open(destino, "w", encoding="utf-8", newline="") as archivo:
        archivo.write(contenido)
    return destino


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------


def main() -> None:
    base = Path(__file__).resolve().parent / CARPETA_CODIGOS

    print("=" * 62)
    print("  GENERADOR DE CONSULTAS .qry PARA iQuery")
    print(f"  Subject: {SUBJECT}")
    print(f"  Carpeta destino: {base}")
    print("=" * 62)

    inicio = fin = None
    discnums: list[str] = []
    carpeta = None
    generados: list[Path] = []

    while True:
        numero = len(generados) + 1
        print("\n" + "=" * 62)
        print(f"  CONSULTA #{numero}")
        print("=" * 62)

        # --- Fechas ---
        if inicio and fin and pedir_si_no(
            f"\n¿Uso las mismas fechas ({inicio.isoformat()} a {fin.isoformat()})?"
        ):
            print(f"  Fechas: {inicio.isoformat()} a {fin.isoformat()}")
        else:
            inicio, fin = pedir_rango_fechas()

        # --- Productos ---
        if discnums and pedir_si_no(f"\n¿Uso los mismos productos ({', '.join(discnums)})?"):
            print(f"  Productos: {', '.join(discnums)}")
        else:
            discnums = pedir_discnums()

        # --- Carpeta ---
        if carpeta and pedir_si_no(f"\n¿Guardo en la misma carpeta ('{carpeta.name}')?"):
            pass
        else:
            carpeta = elegir_carpeta(base)

        # --- Generar ---
        contenido = construir_qry(inicio, fin, discnums)
        destino = guardar(contenido, carpeta, nombre_archivo(discnums, inicio, fin))
        generados.append(destino)

        print("\n  ✔ Archivo generado:")
        print(f"    {destino}")
        print(f"    Productos : {', '.join(discnums)}")
        print(f"    Periodo   : {inicio.isoformat()}  a  {fin.isoformat()}")

        if not pedir_si_no("\n¿Generar otra consulta?"):
            break

    print("\n" + "=" * 62)
    print(f"  LISTO: {len(generados)} archivo(s) generado(s)")
    for archivo in generados:
        print(f"    - {archivo.parent.name}/{archivo.name}")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
