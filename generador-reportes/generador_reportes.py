# -*- coding: utf-8 -*-
"""
Generador de un .BAT con varios reportes REPORTSW (PosiTouch).

REPORTSW recibe el periodo del reporte como "hace cuantos dias":

    REPORTSW 8 C 15 13 N 4 YYYY... N Y 1 N N
                    ^  ^
                    |  +-- fin    = hace 13 dias
                    +----- inicio = hace 15 dias

Este programa pide, una por una, las fechas reales (dia/mes/año) de cada
reporte que se quiera sacar, calcula "hace cuantos dias" son contra la
fecha de hoy (segun el reloj de la computadora) y arma un UNICO .BAT con
todos los reportes en orden.

Ese .BAT, al ejecutarse en la maquina de PosiTouch, corre el primer
reporte y se detiene a preguntar "Continuar con el siguiente? (S/N)"; si
se contesta que si, corre el segundo, y asi sucesivamente. Eso da tiempo
a guardar/renombrar cada reporte antes de que se genere el siguiente.
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

PRIMER_ANIO = 2000               # año mas antiguo que se acepta al teclear

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

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))
SALTO = "\r\n"


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


def reportes_txt(n):
    """'1 reporte' / '5 reportes'."""
    return "1 reporte" if n == 1 else "%d reportes" % n


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
# Plantilla: separarla en cabecera / cuerpo repetible / cierre
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


def analizar_plantilla(plantilla):
    """Divide la plantilla en cabecera / cuerpo repetible / cierre.

    cabecera: todo lo que va antes de la linea REPORTSW (se escribe una
              sola vez: @echo off, cd /d C:\\SC, el mkdir, etc).
    cuerpo:   la linea REPORTSW (con su comentario de arriba, si tiene) y
              lo que sigue hasta antes de 'exit' -- esto se repite una vez
              por cada reporte que se pida.
    cierre:   la linea 'exit' en adelante.
    """
    coincidencia = PATRON_REPORTSW.search(plantilla)
    if not coincidencia:
        raise ValueError(
            "No se encontro una linea 'REPORTSW <n> <n>' dentro de %s"
            % ARCHIVO_PLANTILLA)

    lineas = plantilla.splitlines(True)

    acumulado = 0
    idx_reportsw = len(lineas) - 1
    for i, linea in enumerate(lineas):
        if acumulado <= coincidencia.start() < acumulado + len(linea):
            idx_reportsw = i
            break
        acumulado += len(linea)

    inicio_cuerpo = idx_reportsw
    if inicio_cuerpo > 0 and lineas[inicio_cuerpo - 1].strip().upper().startswith("REM"):
        inicio_cuerpo -= 1

    idx_exit = len(lineas)
    for i in range(idx_reportsw, len(lineas)):
        if lineas[i].strip().lower() == "exit":
            idx_exit = i
            break

    cabecera = "".join(lineas[:inicio_cuerpo])
    cuerpo = "".join(lineas[inicio_cuerpo:idx_exit])
    cierre = "".join(lineas[idx_exit:])
    if not cierre.strip():
        cierre = "exit" + SALTO

    return cabecera, cuerpo, cierre


def sustituir_dias(texto, dias_inicio, dias_fin):
    """Cambia los dos numeros de la linea REPORTSW dentro de 'texto'."""
    def reemplazo(m):
        return "%s%d%s%d" % (m.group(1), dias_inicio, m.group(3), dias_fin)

    nuevo, cuantos = PATRON_REPORTSW.subn(reemplazo, texto)
    if cuantos == 0:
        raise ValueError("No se encontro la linea REPORTSW para sustituir.")
    return nuevo


# --------------------------------------------------------------------------
# Armar el .BAT con todos los reportes pedidos
# --------------------------------------------------------------------------

def insertar_tras_echo_off(texto, lineas_extra):
    """Inserta 'lineas_extra' justo despues de '@echo off'."""
    lineas = texto.splitlines(True)
    posicion = 0
    for i, linea in enumerate(lineas):
        if linea.strip().lower().lstrip("@") == "echo off":
            posicion = i + 1
            break
    bloque = [l + SALTO for l in lineas_extra] + [SALTO]
    lineas[posicion:posicion] = bloque
    return "".join(lineas)


def construir_bat(cabecera, cuerpo, cierre, periodos, hoy):
    """Arma el .BAT completo con todos los periodos, uno tras otro.

    Con un solo periodo no hace falta pausa ni pregunta: corre directo.
    Con dos o mas, cada reporte termina preguntando si se continua con el
    siguiente (S/N); si se contesta que no, el .BAT se cierra ahi mismo.
    """
    n = len(periodos)

    resumen = [
        "REM ---------------------------------------------------------------",
        "REM %s generado%s el %s" % (reportes_txt(n), "" if n == 1 else "s",
                                     hoy.strftime("%d/%m/%Y")),
    ]
    for i, p in enumerate(periodos, start=1):
        resumen.append(
            "REM   %d) %s al %s  (hace %s .. hace %s)"
            % (i, p["inicio"].strftime("%d/%m/%Y"), p["fin"].strftime("%d/%m/%Y"),
               dias_txt(p["dias_inicio"]), dias_txt(p["dias_fin"])))
    resumen.append(
        "REM Solo es valido si se ejecuta el mismo dia en que se genero.")
    resumen.append(
        "REM ---------------------------------------------------------------")

    texto = insertar_tras_echo_off(cabecera, resumen)

    for i, p in enumerate(periodos, start=1):
        if i > 1:
            texto += ":reporte%d" % i + SALTO
        texto += SALTO
        if n > 1:
            texto += "echo." + SALTO
            texto += "echo ===============================================" + SALTO
            texto += ("echo  Reporte %d de %d : %s al %s"
                       % (i, n, p["inicio"].strftime("%d/%m/%Y"),
                          p["fin"].strftime("%d/%m/%Y"))) + SALTO
            texto += "echo ===============================================" + SALTO

        cuerpo_reporte = sustituir_dias(cuerpo, p["dias_inicio"], p["dias_fin"])
        if not cuerpo_reporte.endswith(("\n", "\r")):
            cuerpo_reporte += SALTO
        texto += cuerpo_reporte

        if i < n:
            texto += SALTO
            texto += ("echo  Reporte %d listo. Guarda o renombra el archivo"
                       " generado." % i) + SALTO
            texto += SALTO
            texto += ('choice /c SN /n /m "  Continuar con el reporte %d de'
                       ' %d (S/N)? "' % (i + 1, n)) + SALTO
            texto += "if errorlevel 2 goto :fin" + SALTO
            texto += "goto :reporte%d" % (i + 1) + SALTO
        elif n > 1:
            texto += SALTO
            texto += ("echo  Reporte %d listo. Ya se generaron los %d"
                       " reportes." % (i, n)) + SALTO
            texto += SALTO

    texto += ":fin" + SALTO
    texto += cierre
    return texto


def nombre_archivo(periodos):
    inicio = periodos[0]["inicio"]
    fin = periodos[-1]["fin"]
    nombre = "%s%s%s" % (inicio.strftime("%d-%m-%y"), SEPARADOR_NOMBRE,
                         fin.strftime("%d-%m-%y"))
    if len(periodos) > 1:
        nombre += " (%d reportes)" % len(periodos)
    return nombre + ".bat"


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


def recolectar_periodos(hoy):
    """Pregunta periodos uno por uno para armar UN solo .BAT.

    Devuelve la lista de periodos (vacia si se cancela sin cargar nada).
    """
    periodos = []
    while True:
        print("-" * 66)
        print(" Reporte %d" % (len(periodos) + 1))
        print()

        periodo = pedir_periodo(hoy)
        if periodo is None:
            break
        inicio, fin = periodo

        dias_inicio = dias_desde_hoy(inicio, hoy)
        dias_fin = dias_desde_hoy(fin, hoy)

        print()
        print("  Periodo : %s  ->  %s  (%s)"
              % (inicio.strftime("%d/%m/%Y"), fin.strftime("%d/%m/%Y"),
                 dias_txt((fin - inicio).days + 1)))
        print("  Inicio  : hace %s" % dias_txt(dias_inicio))
        print("  Fin     : hace %s" % dias_txt(dias_fin))
        print()

        periodos.append({
            "inicio": inicio, "fin": fin,
            "dias_inicio": dias_inicio, "dias_fin": dias_fin,
        })

        if not preguntar_si_no("  Agregar otro reporte a este mismo archivo .BAT?"):
            break
        print()

    return periodos


def main():
    cabecera, cuerpo, cierre = analizar_plantilla(leer_plantilla())

    print("=" * 66)
    print(" GENERADOR DE REPORTES REPORTSW")
    print("=" * 66)
    print(" Se piden dia, mes y año por separado; solo numeros (15, 8, 2026).")
    print(" El año puede ir completo (2026) o de dos digitos (26).")
    print(" Atajo: escribe 'hoy', 'ayer' o 'anteayer' en el dia.")
    print(" Escribe 'salir' en cualquier pregunta para terminar.")
    print()
    print(" Cada reporte que agregues va al MISMO archivo .BAT. Al ejecutarlo")
    print(" en la maquina de PosiTouch corre el primero, se detiene a")
    print(" preguntar si sigues con el siguiente (S/N), y asi con todos.")
    print()

    archivos_generados = 0

    while True:
        hoy = datetime.date.today()   # se relee por si cambia el dia entre corridas
        print("=" * 66)
        print(" Hoy es %s" % hoy.strftime("%d/%m/%Y"))
        print()

        periodos = recolectar_periodos(hoy)

        if periodos:
            try:
                contenido = construir_bat(cabecera, cuerpo, cierre, periodos, hoy)
            except ValueError as error:
                print("\n  ERROR: %s\n" % error)
                break

            ruta = guardar(contenido, nombre_archivo(periodos))
            archivos_generados += 1

            print()
            print("  Archivo .BAT con %d reporte(s): %s%s%s"
                  % (len(periodos), CARPETA_SALIDA, os.sep, os.path.basename(ruta)))
            if len(periodos) > 1:
                print("  Al ejecutarlo, cada reporte se detiene a preguntar si")
                print("  sigues con el siguiente (S/N) antes de continuar.")
            print()

        if not periodos or not preguntar_si_no(
                "¿Generar otro archivo .BAT (para otras fechas)?"):
            break
        print()

    print()
    print("=" * 66)
    print(" Listo. Archivos .BAT generados en esta sesion: %d" % archivos_generados)
    if archivos_generados:
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
