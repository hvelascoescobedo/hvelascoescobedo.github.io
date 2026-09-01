# -*- coding: utf-8 -*-
"""
Generador de archivos .BAT para reportes REPORTSW (PosiTouch).

REPORTSW recibe el periodo del reporte como "hace cuantos dias":

    REPORTSW 8 C 15 13 N 4 YYYY... N Y 1 N N
                    ^  ^
                    |  +-- fin   = hace 13 dias
                    +----- inicio = hace 15 dias

Este programa pide las fechas reales (dia, mes y año), calcula cuantos dias
han pasado desde hoy (segun el reloj de la computadora) y escribe un .BAT
nuevo con esos numeros ya corregidos.
"""

import datetime
import os
import re
import sys

# --------------------------------------------------------------------------
# Configuracion (cambiar aqui si hace falta)
# --------------------------------------------------------------------------

CARPETA_SALIDA = "ejeutables"   # carpeta donde se guardan los .BAT generados
ARCHIVO_PLANTILLA = "plantilla.BAT"

# Windows no permite "/" en nombres de archivo, se usa este separador.
SEPARADOR_NOMBRE = " a "        # -> "15-08-26 a 17-08-26.bat"

# Plantilla de respaldo por si plantilla.BAT no esta en la carpeta.
PLANTILLA_POR_DEFECTO = "\r\n".join([
    "@echo off",
    "setlocal",
    "",
    "REM Ir a la carpeta de PosiTouch",
    "cd /d C:\\SC",
    "",
    "REM Crear carpeta para reportes si no existe",
    "if not exist C:\\PosiReports mkdir C:\\PosiReports",
    "",
    "REM Ejecutar reporte VENTAS",
    "REPORTSW 8 C 15 13 N 4 YYYYYYYYYYYYYYYYYYYYY N Y 1 N N",
    "",
    "REM Esperar a que termine",
    "timeout /t 10 /nobreak >nul",
    "",
    "exit",
    "",
])

# Captura: prefijo "REPORTSW 8 C ", numero inicio, espacios, numero fin.
PATRON_REPORTSW = re.compile(
    r"(?im)^([ \t]*REPORTSW[ \t]+\S+[ \t]+\S+[ \t]+)(\d+)([ \t]+)(\d+)"
)

PRIMER_ANIO = 2000              # año mas antiguo que se acepta al teclear

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------
# Fechas
# --------------------------------------------------------------------------

CANCELAR = "__cancelar__"
ATAJOS = {"hoy": 0, "ayer": 1, "anteayer": 2}


def leer_numero(etiqueta, minimo, maximo, con_atajos=False):
    """Pide un numero entre minimo y maximo.

    Devuelve el numero, la palabra del atajo ('hoy', 'ayer'...) o CANCELAR.
    """
    while True:
        texto = input("  %-15s: " % etiqueta).strip()

        if texto.lower() in ("salir", "cancelar", "q"):
            return CANCELAR
        if con_atajos and texto.lower() in ATAJOS:
            return texto.lower()

        try:
            numero = int(texto)
        except ValueError:
            print("     -> Escribe solo numeros, del %d al %d." % (minimo, maximo))
            continue

        if not minimo <= numero <= maximo:
            print("     -> Tiene que estar entre %d y %d." % (minimo, maximo))
            continue

        return numero


def leer_anio(etiqueta, hoy):
    """Pide el año. Acepta 2026 o 26. Devuelve el año o CANCELAR."""
    while True:
        valor = leer_numero(etiqueta, 0, 9999)
        if valor == CANCELAR:
            return CANCELAR

        anio = valor + 2000 if valor < 100 else valor
        if not PRIMER_ANIO <= anio <= hoy.year:
            print("     -> Escribe el año completo (%d) o sus dos ultimos"
                  " digitos (%s)." % (hoy.year, hoy.strftime("%y")))
            continue

        return anio


def leer_fecha(cual, hoy):
    """Pide dia, mes y año por separado. Devuelve un date o None si se cancela."""
    while True:
        dia = leer_numero("Día de %s" % cual, 1, 31, con_atajos=True)
        if dia == CANCELAR:
            return None
        if dia in ATAJOS:
            fecha = hoy - datetime.timedelta(days=ATAJOS[dia])
            print("     -> %s" % fecha.strftime("%d/%m/%Y"))
            return fecha

        mes = leer_numero("Mes de %s" % cual, 1, 12)
        if mes == CANCELAR:
            return None

        anio = leer_anio("Año de %s" % cual, hoy)
        if anio == CANCELAR:
            return None

        try:
            fecha = datetime.date(anio, mes, dia)
        except ValueError:
            print("     -> El %d/%d/%d no existe en el calendario."
                  " Vamos de nuevo.\n" % (dia, mes, anio))
            continue

        if fecha > hoy:
            print("     -> El %s es del futuro (hoy es %s). REPORTSW solo mira"
                  " hacia atras. Vamos de nuevo.\n"
                  % (fecha.strftime("%d/%m/%Y"), hoy.strftime("%d/%m/%Y")))
            continue

        print("     -> %s" % fecha.strftime("%d/%m/%Y"))
        return fecha


def dias_desde_hoy(fecha, hoy):
    """Cuantos dias han pasado desde 'fecha' hasta hoy. Hoy = 0, ayer = 1."""
    return (hoy - fecha).days


def dias_txt(n):
    """'1 dia' / '5 dias', para que los mensajes se lean bien."""
    return "1 dia" if n == 1 else "%d dias" % n


def pedir_periodo(hoy):
    """Devuelve (fecha_inicio, fecha_fin) o None si el usuario cancela."""
    while True:
        inicio = leer_fecha("inicio", hoy)
        if inicio is None:
            return None
        print()

        fin = leer_fecha("fin", hoy)
        if fin is None:
            return None

        if inicio > fin:
            print("\n     -> La fecha de inicio es posterior a la de fin.")
            if preguntar_si_no("        Invertirlas?"):
                inicio, fin = fin, inicio
            else:
                print()
                continue

        return inicio, fin


# --------------------------------------------------------------------------
# Generacion del .BAT
# --------------------------------------------------------------------------

def leer_plantilla():
    """Lee plantilla.BAT respetando su codificacion original."""
    ruta = os.path.join(CARPETA_BASE, ARCHIVO_PLANTILLA)
    if not os.path.exists(ruta):
        print("Aviso: no se encontro '%s', se usa la plantilla interna.\n"
              % ARCHIVO_PLANTILLA)
        return PLANTILLA_POR_DEFECTO

    with open(ruta, "rb") as f:
        crudo = f.read()
    for codificacion in ("utf-8", "cp1252", "latin-1"):
        try:
            return crudo.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return crudo.decode("latin-1")


def construir_bat(plantilla, inicio, fin, dias_inicio, dias_fin, hoy):
    """Sustituye los dos numeros de la linea REPORTSW y agrega un encabezado."""
    coincidencia = PATRON_REPORTSW.search(plantilla)
    if not coincidencia:
        raise ValueError(
            "No se encontro una linea 'REPORTSW <n> <n>' dentro de %s"
            % ARCHIVO_PLANTILLA)

    original = coincidencia.group(0)
    nueva = "%s%d%s%d" % (coincidencia.group(1), dias_inicio,
                          coincidencia.group(3), dias_fin)
    texto = plantilla[:coincidencia.start()] + nueva + plantilla[coincidencia.end():]

    encabezado = [
        "REM ---------------------------------------------------------------",
        "REM Reporte de ventas del %s al %s"
        % (inicio.strftime("%d/%m/%Y"), fin.strftime("%d/%m/%Y")),
        "REM Equivale a: hace %s .. hace %s"
        % (dias_txt(dias_inicio), dias_txt(dias_fin)),
        "REM Generado el %s - solo valido si se ejecuta ese mismo dia."
        % hoy.strftime("%d/%m/%Y"),
        "REM ---------------------------------------------------------------",
    ]

    lineas = texto.splitlines(True)
    salto = "\r\n"
    posicion = 0
    for i, linea in enumerate(lineas):
        if linea.strip().lower().lstrip("@") == "echo off":
            posicion = i + 1
            break
    bloque = [l + salto for l in encabezado] + [salto]
    lineas[posicion:posicion] = bloque
    return "".join(lineas), original.strip(), nueva.strip()


def nombre_archivo(inicio, fin):
    return "%s%s%s.bat" % (inicio.strftime("%d-%m-%y"),
                           SEPARADOR_NOMBRE,
                           fin.strftime("%d-%m-%y"))


def guardar(contenido, nombre):
    """Escribe el .BAT en la carpeta de salida con saltos de linea de Windows."""
    carpeta = os.path.join(CARPETA_BASE, CARPETA_SALIDA)
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)

    ruta = os.path.join(carpeta, nombre)
    if os.path.exists(ruta):
        print("\n  Ya existe '%s' en la carpeta %s." % (nombre, CARPETA_SALIDA))
        if not preguntar_si_no("  Sobrescribirlo?"):
            base, extension = os.path.splitext(nombre)
            n = 2
            while os.path.exists(ruta):
                ruta = os.path.join(carpeta, "%s (%d)%s" % (base, n, extension))
                n += 1

    datos = contenido.replace("\r\n", "\n").replace("\n", "\r\n")
    try:
        codificado = datos.encode("cp1252")
    except UnicodeEncodeError:
        codificado = datos.encode("utf-8")

    with open(ruta, "wb") as f:
        f.write(codificado)
    return ruta


# --------------------------------------------------------------------------
# Interfaz de consola
# --------------------------------------------------------------------------

def preguntar_si_no(pregunta):
    while True:
        respuesta = input("%s (s/n): " % pregunta).strip().lower()
        if respuesta in ("s", "si", "sí", "y", "yes"):
            return True
        if respuesta in ("n", "no"):
            return False


def main():
    plantilla = leer_plantilla()

    print("=" * 66)
    print(" GENERADOR DE REPORTES REPORTSW")
    print("=" * 66)
    print(" Se piden dia, mes y año por separado; solo numeros (15, 8, 2026).")
    print(" El año puede ir completo (2026) o de dos digitos (26).")
    print(" Atajo: escribe 'hoy', 'ayer' o 'anteayer' en el dia.")
    print(" Escribe 'salir' en cualquier pregunta para terminar.")
    print()

    generados = 0

    while True:
        hoy = datetime.date.today()   # se relee en cada vuelta por si cambia el dia
        print("-" * 66)
        print(" Hoy es %s" % hoy.strftime("%d/%m/%Y"))
        print()

        periodo = pedir_periodo(hoy)
        if periodo is None:
            break
        inicio, fin = periodo

        dias_inicio = dias_desde_hoy(inicio, hoy)
        dias_fin = dias_desde_hoy(fin, hoy)

        try:
            contenido, linea_vieja, linea_nueva = construir_bat(
                plantilla, inicio, fin, dias_inicio, dias_fin, hoy)
        except ValueError as error:
            print("\n  ERROR: %s\n" % error)
            break

        print()
        print("  Periodo : %s  ->  %s  (%s)"
              % (inicio.strftime("%d/%m/%Y"), fin.strftime("%d/%m/%Y"),
                 dias_txt((fin - inicio).days + 1)))
        print("  Inicio  : hace %s" % dias_txt(dias_inicio))
        print("  Fin     : hace %s" % dias_txt(dias_fin))
        print("  Antes   : %s" % linea_vieja)
        print("  Ahora   : %s" % linea_nueva)

        ruta = guardar(contenido, nombre_archivo(inicio, fin))
        generados += 1
        print("\n  Guardado en: %s%s%s"
              % (CARPETA_SALIDA, os.sep, os.path.basename(ruta)))
        print()

        if not preguntar_si_no("  Generar otro reporte?"):
            break
        print()

    print()
    print("=" * 66)
    print(" Listo. Archivos generados en esta sesion: %d" % generados)
    if generados:
        print(" Carpeta: %s" % os.path.join(CARPETA_BASE, CARPETA_SALIDA))
        print(" Recuerda: los numeros son 'dias desde hoy', asi que cada .BAT")
        print(" debe ejecutarse el mismo dia en que se genero.")
    print("=" * 66)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nCancelado.")
        sys.exit(0)
