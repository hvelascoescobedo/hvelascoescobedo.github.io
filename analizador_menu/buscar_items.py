#!/usr/bin/env python3
"""Buscador interactivo de ventas por item en los reportes de los restaurantes.

Uso interactivo (el programa pregunta todo lo que necesita):

    python buscar_items.py

Uso directo desde la terminal (sin preguntas):

    python buscar_items.py --carpeta datos --items 37014,37021 --salida ventas.xlsx
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

# El motor del programa vive en la carpeta "sistema" para no estorbar aqui.
CARPETA_BASE = Path(__file__).resolve().parent
CARPETA_SISTEMA = CARPETA_BASE / "sistema"
sys.path.insert(0, str(CARPETA_SISTEMA))

from analizador.busqueda import buscar_items, cargar_reportes, normalizar_busquedas
from analizador.diccionario import DiccionarioRestaurantes
from analizador.exportar_excel import (
    MAXIMO_HOJAS_COMBINACION,
    contar_combinaciones,
    exportar_resultados,
)

CARPETA_POR_DEFECTO = "datos"
COMILLAS = "\"'\u201c\u201d\u2018\u2019\u00ab\u00bb"


# ---------------------------------------------------------------------------
# Ayudas de terminal
# ---------------------------------------------------------------------------


def _limpiar_ruta(texto: str) -> str:
    """Acepta la ruta con o sin comillas.

    Windows copia las rutas como "C:\\Users\\...\\Hora Bostons"; se quitan las
    comillas (rectas o tipograficas) y los espacios sobrantes de los extremos.
    """
    limpio = texto.strip()
    while len(limpio) >= 2 and limpio[0] in COMILLAS and limpio[-1] in COMILLAS:
        limpio = limpio[1:-1].strip()
    return limpio.strip(COMILLAS).strip()


def _titulo(texto: str) -> None:
    print()
    print("=" * 70)
    print(texto)
    print("=" * 70)


def _preguntar(mensaje: str, por_defecto: str = "") -> str:
    sufijo = f" [{por_defecto}]" if por_defecto else ""
    try:
        respuesta = _limpiar_ruta(input(f"{mensaje}{sufijo}: "))
    except EOFError:
        return por_defecto
    return respuesta or por_defecto


def _pedir_carpeta(inicial: str | None) -> Path:
    """Devuelve la carpeta de reportes; si no vino por --carpeta, la pregunta."""
    base = CARPETA_BASE
    if inicial:
        candidata = _limpiar_ruta(inicial)
    else:
        candidata = _preguntar(
            "Carpeta con los archivos .txt de los reportes", CARPETA_POR_DEFECTO
        )
    while True:
        carpeta = Path(candidata).expanduser()
        if not carpeta.is_absolute() and not carpeta.exists():
            carpeta = base / candidata
        if carpeta.is_dir():
            return carpeta
        print(f"  No encontre la carpeta '{candidata}'.")
        candidata = _preguntar("Carpeta con los archivos .txt de los reportes")
        if not candidata:
            raise SystemExit("Sin carpeta que procesar. Salgo.")


def _pedir_items(items_cli: str | None) -> list[str]:
    if items_cli:
        busquedas = normalizar_busquedas([items_cli])
        if busquedas:
            return busquedas
    print()
    print("Escribe el o los items que quieres buscar, separados por comas.")
    print("  Ejemplos:  37014            (un item)")
    print("             37014, 37021     (varios items)")
    print("             37014-37020      (un rango de numeros)")
    print("             alitas           (texto: busca por nombre del producto)")
    while True:
        entrada = _preguntar("Item(s) a buscar")
        busquedas = normalizar_busquedas([entrada])
        if busquedas:
            return busquedas
        print("  No entendi nada. Intenta de nuevo.")


def _rango_fechas(renglon) -> str:
    """Periodo del reporte en texto: 'del 03/08/2026 al 06/08/2026'."""
    if renglon.fecha_inicio and renglon.fecha_fin:
        return f"del {renglon.fecha_inicio:%d/%m/%Y} al {renglon.fecha_fin:%d/%m/%Y}"
    return "(sin fechas en el reporte)"


def _avance(numero: int, total: int, ruta: Path) -> None:
    print(f"  [{numero:>3}/{total}] {ruta.name}")


def _mostrar_resumen(resultados, busquedas) -> None:
    _titulo("RESUMEN EN PANTALLA")
    for termino in busquedas:
        renglones = [r for r in resultados if r.busqueda == termino]
        con_venta = [r for r in renglones if r.unidades_vendidas]
        total_unidades = sum(r.unidades_vendidas for r in renglones)
        total_importe = sum(r.ventas_importe for r in renglones)
        nombre = next((r.item_nombre for r in renglones if r.item_nombre), "(sin coincidencias)")
        print(f"\nItem '{termino}' - {nombre}")
        print(f"  Restaurantes/periodos con venta: {len(con_venta)}")
        print(f"  Unidades vendidas (total):       {total_unidades:,}")
        print(f"  Importe vendido (total):         ${total_importe:,.2f}")

        principales = sorted(con_venta, key=lambda r: r.unidades_vendidas, reverse=True)[:5]
        if principales:
            print("  Mayores ventas:")
            for renglon in principales:
                etiqueta = f"{renglon.restaurante_id} {renglon.restaurante_nombre}".strip()
                print(
                    f"    {etiqueta:<32} {_rango_fechas(renglon):<24} "
                    f"{renglon.unidades_vendidas:>6} uds  ${renglon.ventas_importe:>12,.2f}"
                )


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------


def construir_argumentos() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Busca cuantas ventas tuvo un item en todos los reportes de una carpeta.",
    )
    parser.add_argument("--carpeta", help="Carpeta con los archivos .txt (por defecto: datos)")
    parser.add_argument("--items", help="Items a buscar separados por comas (ej. 37014,37021)")
    parser.add_argument("--salida", help="Nombre del archivo Excel de resultados")
    parser.add_argument("--diccionario", help="Ruta del Diccionario_restaurantes.xlsx")
    parser.add_argument(
        "--sin-vacios",
        action="store_true",
        help="No incluir los restaurantes donde el item no aparece",
    )
    parser.add_argument(
        "--no-recursivo",
        action="store_true",
        help="Leer solo la carpeta indicada, sin entrar a las subcarpetas",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    argumentos = construir_argumentos().parse_args(argv)
    base = CARPETA_BASE

    _titulo("BUSCADOR DE VENTAS POR ITEM")

    carpeta = _pedir_carpeta(argumentos.carpeta)
    print(f"Carpeta de reportes: {carpeta}")

    # Diccionario de restaurantes (#ID -> nombre).
    diccionario = None
    if argumentos.diccionario:
        diccionario = DiccionarioRestaurantes.desde_excel(_limpiar_ruta(argumentos.diccionario))
    else:
        for lugar in (carpeta, CARPETA_SISTEMA, base, base / "datos"):
            diccionario = DiccionarioRestaurantes.localizar(lugar)
            if diccionario:
                break
    if diccionario:
        print(f"Diccionario de restaurantes: {len(diccionario)} restaurantes cargados")
    else:
        diccionario = DiccionarioRestaurantes()
        print("Diccionario de restaurantes: no encontrado (se usara el nombre del reporte)")

    # Lectura de todos los archivos de la carpeta.
    print("\nLeyendo archivos...")
    registros = cargar_reportes(
        carpeta, recursivo=not argumentos.no_recursivo, al_avanzar=_avance
    )
    if not registros:
        print("\nNo hay archivos de reporte (.txt) en esa carpeta.")
        return 1

    correctos = [r for r in registros if r.reporte]
    fallidos = [r for r in registros if not r.reporte]
    periodos = sorted({r.periodo_fechas for r in correctos if r.periodo_fechas})
    restaurantes = sorted({r.restaurante_id for r in correctos if r.restaurante_id})
    print(
        f"\nArchivos leidos: {len(correctos)} | restaurantes: {len(restaurantes)} "
        f"| periodos (segun el reporte): "
        f"{', '.join(periodos) if periodos else 'sin identificar'}"
    )
    for registro in fallidos:
        print(f"  AVISO: no se pudo leer {registro.info.nombre_archivo}: {registro.error}")
    for registro in correctos:
        if registro.aviso_periodo:
            print(f"  AVISO en {registro.info.nombre_archivo}: {registro.aviso_periodo}")

    # Busqueda (puede repetirse varias veces en la misma sesion).
    interactivo = not (argumentos.items and argumentos.salida)
    while True:
        busquedas = _pedir_items(argumentos.items)
        print(f"\nBuscando {len(busquedas)} item(s) en {len(correctos)} archivo(s)...")
        resultados = buscar_items(
            registros,
            busquedas,
            diccionario=diccionario,
            incluir_no_encontrados=not argumentos.sin_vacios,
        )

        _mostrar_resumen(resultados, busquedas)

        marca = datetime.now().strftime("%Y%m%d_%H%M")
        salida_por_defecto = argumentos.salida or f"ventas_items_{marca}.xlsx"
        if interactivo:
            salida = _preguntar("\nNombre del archivo de Excel", salida_por_defecto)
        else:
            salida = salida_por_defecto
        ruta_salida = Path(_limpiar_ruta(salida)).expanduser()
        if not ruta_salida.is_absolute():
            ruta_salida = base / "resultados" / ruta_salida

        combinaciones = contar_combinaciones(resultados)
        ruta_final = exportar_resultados(resultados, ruta_salida, registros)
        print(f"\nListo. Excel generado en:\n  {ruta_final}")
        hojas = min(combinaciones, MAXIMO_HOJAS_COMBINACION)
        print(f"  Hojas de producto x periodo: {hojas}")
        if combinaciones > MAXIMO_HOJAS_COMBINACION:
            print(
                f"  AVISO: eran {combinaciones} combinaciones y solo se armaron las primeras "
                f"{MAXIMO_HOJAS_COMBINACION}; la hoja Resultados si trae todo."
            )

        if not interactivo:
            break
        argumentos.items = None
        if _preguntar("\n¿Buscar otros items? (s/n)", "n").lower() not in {"s", "si", "sí", "y"}:
            break

    print("\nHasta luego.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
