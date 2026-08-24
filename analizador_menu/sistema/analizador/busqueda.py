"""Busqueda de items a lo largo de todos los reportes de una carpeta.

Flujo: se listan los archivos de la carpeta, se toma el #restaurante del nombre
del archivo, se lee su contenido y se buscan los items solicitados.  Las fechas
del periodo se leen SIEMPRE de dentro del reporte ("For the period: 8/3/26 to
8/6/26"), nunca del nombre del archivo.  El resultado es una lista de renglones
listos para exportar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Iterable, Sequence

from .diccionario import DiccionarioRestaurantes
from .nombre_archivo import InfoArchivo, interpretar_nombre, listar_archivos
from .parser_reporte import ItemMenu, ReporteMenu, leer_reporte

RE_SOLO_DIGITOS = re.compile(r"^\d+$")


@dataclass
class RegistroArchivo:
    """Registro de un archivo procesado (archivo + metadatos + contenido)."""

    info: InfoArchivo
    reporte: ReporteMenu | None
    error: str = ""

    @property
    def restaurante_id(self) -> str:
        """#ID del restaurante: primero el del nombre, luego el del encabezado."""
        if self.info.restaurante_id:
            return self.info.restaurante_id
        if self.reporte and self.reporte.restaurante_id:
            return self.reporte.restaurante_id
        return ""

    @property
    def fecha_inicio(self) -> date | None:
        """Fecha inicial del periodo, tomada de DENTRO del reporte."""
        return self.reporte.fecha_inicio if self.reporte else None

    @property
    def fecha_fin(self) -> date | None:
        """Fecha final del periodo, tomada de DENTRO del reporte."""
        return self.reporte.fecha_fin if self.reporte else None

    @property
    def periodo_fechas(self) -> str:
        """Etiqueta corta del periodo del reporte, para mostrar en pantalla."""
        if self.fecha_inicio and self.fecha_fin:
            return f"{self.fecha_inicio:%d/%m/%Y}-{self.fecha_fin:%d/%m/%Y}"
        return ""

    @property
    def aviso_periodo(self) -> str:
        """Avisa si el nombre del archivo no coincide con las fechas del reporte.

        Las fechas buenas son siempre las del reporte; esto solo sirve para
        detectar un archivo mal nombrado al momento de descargarlo.
        """
        info, dias_reporte = self.info, (self.fecha_inicio, self.fecha_fin)
        if info.dia_inicio is None or not all(dias_reporte):
            return ""
        if (info.dia_inicio, info.dia_fin) != (self.fecha_inicio.day, self.fecha_fin.day):
            return (
                f"El nombre dice '{info.periodo_normalizado}' pero el reporte "
                f"es del {self.fecha_inicio:%d/%m/%Y} al {self.fecha_fin:%d/%m/%Y}"
            )
        return ""


@dataclass
class ResultadoItem:
    """Un renglon del reporte final: item x restaurante x periodo.

    Las fechas del periodo salen del propio reporte ("For the period: ..."),
    no del nombre del archivo.
    """

    restaurante_id: str
    restaurante_nombre: str
    fecha_inicio: date | None
    fecha_fin: date | None
    busqueda: str
    item_numero: int | None
    item_nombre: str
    categoria: str
    subcategoria: str
    unidades_vendidas: int
    ventas_importe: float
    precio_menu: float
    costo_total: float
    utilidad: float
    encontrado: bool
    archivo: str


def cargar_reportes(
    carpeta: str | Path,
    recursivo: bool = True,
    al_avanzar: Callable[[int, int, Path], None] | None = None,
) -> list[RegistroArchivo]:
    """Lee todos los reportes de la carpeta y devuelve un registro por archivo."""
    archivos = listar_archivos(carpeta, recursivo=recursivo)
    registros: list[RegistroArchivo] = []
    total = len(archivos)

    for numero, ruta in enumerate(archivos, start=1):
        if al_avanzar:
            al_avanzar(numero, total, ruta)
        info = interpretar_nombre(ruta)
        try:
            reporte = leer_reporte(ruta)
        except Exception as error:  # archivo corrupto o formato inesperado
            registros.append(RegistroArchivo(info=info, reporte=None, error=str(error)))
            continue
        registros.append(RegistroArchivo(info=info, reporte=reporte))

    return registros


def normalizar_busquedas(entradas: Iterable[str]) -> list[str]:
    """Limpia la lista de items tecleados por el usuario.

    Acepta numeros ("37014"), rangos ("37014-37020") y texto libre para
    buscar por nombre ("alitas").  Devuelve la lista sin duplicados.
    """
    resultado: list[str] = []
    for entrada in entradas:
        for parte in re.split(r"[,;\n]+", str(entrada)):
            parte = parte.strip()
            if not parte:
                continue
            rango = re.fullmatch(r"(\d{2,6})\s*-\s*(\d{2,6})", parte)
            if rango:
                inicio, fin = int(rango.group(1)), int(rango.group(2))
                if inicio <= fin and fin - inicio <= 5000:
                    resultado.extend(str(n) for n in range(inicio, fin + 1))
                    continue
            resultado.append(parte)

    vistos: set[str] = set()
    unicos: list[str] = []
    for termino in resultado:
        clave = termino.upper()
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(termino)
    return unicos


def _coincidencias(reporte: ReporteMenu, termino: str) -> list[ItemMenu]:
    """Items del reporte que corresponden al termino buscado."""
    if RE_SOLO_DIGITOS.match(termino):
        return reporte.buscar_por_numero(int(termino))
    return reporte.buscar_por_nombre(termino)


def buscar_items(
    registros: Sequence[RegistroArchivo],
    busquedas: Sequence[str],
    diccionario: DiccionarioRestaurantes | None = None,
    incluir_no_encontrados: bool = True,
) -> list[ResultadoItem]:
    """Busca los items indicados en todos los archivos ya cargados.

    Con ``incluir_no_encontrados`` se agrega un renglon con 0 ventas cuando el
    item no aparece en el reporte de ese restaurante/periodo, de modo que la
    tabla final quede completa para todos los restaurantes.
    """
    diccionario = diccionario or DiccionarioRestaurantes()
    resultados: list[ResultadoItem] = []

    for registro in registros:
        # Se ignoran los archivos que no se pudieron leer o que no traen items
        # (por ejemplo una nota suelta dentro de la carpeta): asi no ensucian
        # la tabla con renglones en cero. Quedan anotados en la hoja Archivos.
        if registro.reporte is None or not registro.reporte.items:
            continue

        restaurante_id = registro.restaurante_id
        restaurante_nombre = diccionario.nombre(restaurante_id) or (
            registro.reporte.restaurante_encabezado or ""
        )

        for termino in busquedas:
            encontrados = _coincidencias(registro.reporte, termino)

            if not encontrados:
                if incluir_no_encontrados:
                    resultados.append(
                        ResultadoItem(
                            restaurante_id=restaurante_id,
                            restaurante_nombre=restaurante_nombre,
                            fecha_inicio=registro.fecha_inicio,
                            fecha_fin=registro.fecha_fin,
                            busqueda=termino,
                            item_numero=int(termino) if RE_SOLO_DIGITOS.match(termino) else None,
                            item_nombre="",
                            categoria="",
                            subcategoria="",
                            unidades_vendidas=0,
                            ventas_importe=0.0,
                            precio_menu=0.0,
                            costo_total=0.0,
                            utilidad=0.0,
                            encontrado=False,
                            archivo=registro.info.nombre_archivo,
                        )
                    )
                continue

            for item in encontrados:
                resultados.append(
                    ResultadoItem(
                        restaurante_id=restaurante_id,
                        restaurante_nombre=restaurante_nombre,
                        fecha_inicio=registro.fecha_inicio,
                        fecha_fin=registro.fecha_fin,
                        busqueda=termino,
                        item_numero=item.inv,
                        item_nombre=item.nombre,
                        categoria=item.categoria,
                        subcategoria=item.subcategoria,
                        unidades_vendidas=item.unidades_vendidas,
                        ventas_importe=item.ventas,
                        precio_menu=item.precio_menu,
                        costo_total=item.costo_total,
                        utilidad=item.utilidad,
                        encontrado=True,
                        archivo=registro.info.nombre_archivo,
                    )
                )

    resultados.sort(
        key=lambda r: (
            str(r.item_numero if r.item_numero is not None else r.busqueda),
            r.restaurante_id,
            r.fecha_inicio or date.min,
        )
    )
    return resultados
