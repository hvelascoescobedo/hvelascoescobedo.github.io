#!/usr/bin/env python3
"""Buscador interactivo de ventas por item en los reportes de los restaurantes.

En Windows basta con dar doble clic en "Buscar items.bat".  Tambien se puede
llamar a mano:

    python buscar_items.py

Uso directo desde la terminal (sin preguntas):

    python buscar_items.py --carpeta datos --items 37014,37021 --salida ventas.xlsx
"""

from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Aqui viven "datos" y "resultados"; el motor esta en la carpeta "sistema".
CARPETA_BASE = Path(__file__).resolve().parent
CARPETA_SISTEMA = CARPETA_BASE / "sistema"
if getattr(sys, "frozen", False):  # ejecutable creado con PyInstaller
    CARPETA_BASE = Path(sys.executable).resolve().parent
    CARPETA_SISTEMA = CARPETA_BASE / "sistema"
sys.path.insert(0, str(CARPETA_SISTEMA))

ARCHIVO_REQUISITOS = CARPETA_SISTEMA / "requirements.txt"
# (modulo que se importa, paquete que hay que instalar, para que sirve)
REQUISITOS = [
    ("openpyxl", "openpyxl", "generar el Excel de resultados"),
    ("pypdf", "pypdf", "leer los reportes en PDF"),
]


def _faltantes() -> list[tuple[str, str, str]]:
    """Requisitos que no estan instalados en esta computadora."""
    pendientes = []
    for modulo, paquete, para_que in REQUISITOS:
        try:
            importlib.import_module(modulo)
        except ImportError:
            pendientes.append((modulo, paquete, para_que))
    return pendientes


def _asegurar_requisitos() -> None:
    """Revisa las librerias necesarias y ofrece instalarlas al vuelo.

    Se hace antes de importar el resto del programa: si falta una libreria, el
    import de mas abajo tronaria con un mensaje que no le dice nada a nadie.
    """
    if getattr(sys, "frozen", False):  # el .exe ya las trae dentro
        return
    pendientes = _faltantes()
    if not pendientes:
        return

    print()
    print("Faltan algunas librerias para que el programa funcione:")
    for _, paquete, para_que in pendientes:
        print(f"  - {paquete}: sirve para {para_que}")

    orden = [sys.executable, "-m", "pip", "install", *(p for _, p, _ in pendientes)]
    if ARCHIVO_REQUISITOS.exists():
        orden = [sys.executable, "-m", "pip", "install", "-r", str(ARCHIVO_REQUISITOS)]

    try:
        respuesta = input("\n¿Las instalo ahora? (s/n) [s]: ").strip().lower()
    except EOFError:
        respuesta = "s"
    if respuesta in {"", "s", "si", "sí", "y"}:
        print("\nInstalando, espera un momento...\n")
        if subprocess.call(orden) == 0 and not _faltantes():
            print("\nListo, ya quedaron instaladas.\n")
            return
        print("\nNo se pudieron instalar solas.")

    print("\nCorre este comando en la terminal y vuelve a intentar:")
    print(f'  {sys.executable} -m pip install -r "{ARCHIVO_REQUISITOS}"')
    print()
    try:
        input("Presiona Enter para salir...")
    except EOFError:
        pass
    raise SystemExit(1)


_asegurar_requisitos()

from analizador.busqueda import (
    buscar_items,
    cargar_reportes,
    detectar_problemas,
    normalizar_busquedas,
)
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
            "Carpeta con los reportes (.txt o .pdf)", CARPETA_POR_DEFECTO
        )
    while True:
        carpeta = Path(candidata).expanduser()
        if not carpeta.is_absolute() and not carpeta.exists():
            carpeta = base / candidata
        if carpeta.is_dir():
            return carpeta
        print(f"  No encontre la carpeta '{candidata}'.")
        candidata = _preguntar("Carpeta con los reportes (.txt o .pdf)")
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


def _etiqueta_restaurante(registro, diccionario) -> str:
    """'#ID Nombre' del restaurante de un archivo, aunque el ID falte."""
    id_ = registro.restaurante_id or "(sin ID)"
    nombre = diccionario.nombre(registro.restaurante_id) if registro.restaurante_id else ""
    return f"{id_} {nombre}".strip()


def _imprimir_problemas(problemas, diccionario) -> None:
    """Lista, antes de preguntar nada mas, que archivos hay que re-descargar."""
    vacios = [p for p in problemas if p.motivo == "vacio"]
    fallidos = [p for p in problemas if p.motivo == "error"]

    _titulo("ARCHIVOS QUE HAY QUE VOLVER A DESCARGAR")

    if vacios:
        print(
            "Estos reportes se leyeron sin ningun error, pero llegaron VACIOS\n"
            "(sin un solo producto adentro): la descarga salio mal.\n"
        )
        for problema in vacios:
            registro = problema.registro
            print(
                f"  {_etiqueta_restaurante(registro, diccionario):<32} "
                f"{_rango_fechas(registro):<28} {registro.info.nombre_archivo}"
            )

    if fallidos:
        if vacios:
            print()
        print("Estos otros ni siquiera se pudieron abrir:\n")
        for problema in fallidos:
            registro = problema.registro
            print(f"  {_etiqueta_restaurante(registro, diccionario):<32} {registro.info.nombre_archivo}")
            print(f"      -> {registro.error}")

    print(
        "\nVuelve a descargar el reporte de esos restaurantes y corre el "
        "programa otra vez; no hace falta tocar los demas archivos."
    )


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

        negativos = [r for r in renglones if r.ventas_importe < 0]
        if negativos:
            categorias = sorted({r.categoria for r in negativos if r.categoria})
            print(
                "  NOTA: el importe sale en negativo porque asi viene en el reporte:\n"
                "        son promociones, descuentos o cortesias, y el sistema registra\n"
                "        lo que se descuento de la venta. Las unidades vendidas si son\n"
                "        positivas (cuantas veces se aplico)."
            )
            if categorias:
                print(f"        Categoria en el reporte: {', '.join(categorias)}")

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
    parser.add_argument(
        "--carpeta", help="Carpeta con los reportes .txt o .pdf (por defecto: datos)"
    )
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
    # Si ya vinieron los items y el nombre de salida por la terminal, no se
    # pregunta nada: se usa para automatizar (y tampoco se puede detener a
    # esperar una respuesta si aparecen archivos con problemas).
    interactivo = not (argumentos.items and argumentos.salida)

    _titulo("BUSCADOR DE VENTAS POR ITEM")

    carpeta = _pedir_carpeta(argumentos.carpeta)
    print(f"Carpeta de reportes: {carpeta}")

    # Diccionario de restaurantes (#ID -> nombre).
    diccionario = None
    if argumentos.diccionario:
        diccionario = DiccionarioRestaurantes.desde_excel(_limpiar_ruta(argumentos.diccionario))
    else:
        lugares = [carpeta, CARPETA_SISTEMA, base, base / "datos"]
        if getattr(sys, "frozen", False):  # copia incluida dentro del .exe
            lugares.append(Path(getattr(sys, "_MEIPASS", base)))
        for lugar in lugares:
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
        print("\nNo hay archivos de reporte (.txt o .pdf) en esa carpeta.")
        return 1

    correctos = [r for r in registros if r.reporte]
    periodos = sorted({r.periodo_fechas for r in correctos if r.periodo_fechas})
    restaurantes = sorted({r.restaurante_id for r in correctos if r.restaurante_id})
    print(
        f"\nArchivos leidos: {len(correctos)} | restaurantes: {len(restaurantes)} "
        f"| periodos (segun el reporte): "
        f"{', '.join(periodos) if periodos else 'sin identificar'}"
    )
    for registro in correctos:
        if registro.aviso_periodo:
            print(f"  AVISO en {registro.info.nombre_archivo}: {registro.aviso_periodo}")

    # Validacion ANTES de preguntar nada mas: si algun reporte llego vacio o
    # no se pudo leer, se avisa de una vez (no hasta el final, en la hoja
    # Archivos del Excel) para poder re-descargarlo y correr el programa de
    # nuevo sin haber perdido tiempo capturando que items buscar.
    problemas = detectar_problemas(registros)
    if problemas:
        _imprimir_problemas(problemas, diccionario)
        if interactivo:
            seguir = _preguntar(
                "\n¿Aun asi quieres continuar, usando solo los restaurantes que "
                "si se leyeron bien? (s/n)",
                "n",
            )
            if seguir.strip().lower() not in {"s", "si", "sí", "y"}:
                print(
                    "\nListo, no se genero ningun Excel. Vuelve a descargar los "
                    "reportes marcados arriba y corre el programa otra vez."
                )
                return 1

    # Busqueda (puede repetirse varias veces en la misma sesion).
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
