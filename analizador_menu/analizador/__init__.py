"""Analizador de reportes 'Menu Item Food Cost Analysis' de restaurantes.

Modulos:
    parser_reporte  -- lectura de los archivos .txt de ancho fijo
    nombre_archivo  -- interpretacion de nombres como "6001 (3-6).txt"
    diccionario     -- catalogo de restaurantes (#ID -> nombre)
    busqueda        -- busqueda de items en todos los archivos de una carpeta
    exportar_excel  -- generacion del archivo de resultados en Excel
"""

from .parser_reporte import ItemMenu, ReporteMenu, leer_reporte
from .nombre_archivo import InfoArchivo, interpretar_nombre
from .diccionario import DiccionarioRestaurantes
from .busqueda import ResultadoItem, buscar_items, cargar_reportes
from .exportar_excel import MAXIMO_HOJAS_COMBINACION, contar_combinaciones, exportar_resultados

__all__ = [
    "ItemMenu",
    "ReporteMenu",
    "leer_reporte",
    "InfoArchivo",
    "interpretar_nombre",
    "DiccionarioRestaurantes",
    "ResultadoItem",
    "buscar_items",
    "cargar_reportes",
    "exportar_resultados",
    "contar_combinaciones",
    "MAXIMO_HOJAS_COMBINACION",
]
