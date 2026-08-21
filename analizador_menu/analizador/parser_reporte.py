"""Lectura de los reportes 'Menu Item Food Cost Analysis' en formato texto.

El reporte es un listado de ancho fijo paginado: cada pagina repite el
encabezado del restaurante y de las columnas, pero todas las paginas
comparten exactamente las mismas columnas.  Los productos vienen agrupados
por categoria (ej. " 1--STARTERS") y subcategoria (ej. "   1--TEAM PLATTER"),
por lo que el parser arrastra ambas etiquetas hacia cada item.  Los numeros de
grupo van alineados a la derecha ("10--EXTRA TOPPINGS" no lleva sangria y
"  10--OPEN LIQUOR" lleva dos espacios), de modo que el nivel se reconoce por
la columna en la que empiezan los guiones.

Posiciones de las columnas (validadas contra el reporte completo):

    [ 0: 8]  Inv#            [76: 89]  Avg. Unit Cost
    [ 9:25]  Name            [89:100]  Total Cost
    [25:34]  Menu Price      [100:111] Cost %
    [34:45]  #Sold           [111:120] % Cont Margin
    [45:56]  #Del            [120:131] Profit
    [56:67]  Sales
    [67:76]  % of Tot Sls
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Definicion de columnas de ancho fijo
# ---------------------------------------------------------------------------

COLUMNAS = {
    "inv": (0, 8),
    "nombre": (9, 25),
    "precio_menu": (25, 34),
    "num_vendidos": (34, 45),
    "num_eliminados": (45, 56),
    "ventas": (56, 67),
    "pct_ventas_totales": (67, 76),
    "costo_unitario_prom": (76, 89),
    "costo_total": (89, 100),
    "pct_costo": (100, 111),
    "pct_margen_contribucion": (111, 120),
    "utilidad": (120, 131),
}

# Grupos: el numero viene alineado a la derecha, asi que lo que distingue el
# nivel es la columna donde empiezan los guiones, no la sangria:
#   " 1--STARTERS" y "10--EXTRA TOPPINGS"       -> guiones en la columna 2 (categoria)
#   "   1--TEAM PLATTER" y "  10--OPEN LIQUOR"  -> guiones en la columna 4 (subcategoria)
RE_GRUPO = re.compile(r"^(?P<sangria> *)(?P<numero>\d+)(?P<guiones>--)(?P<nombre>\S.*?)\s*$")
COLUMNA_GUIONES_CATEGORIA = 2
# "   37014 PLATO DE EQUIPO    399.00 ..."
RE_ITEM = re.compile(r"^\s{2,}(?P<inv>\d+)\s")
RE_PERIODO = re.compile(
    r"For the period:\s*(?P<inicio>\d{1,2}/\d{1,2}/\d{2,4})\s*to\s*(?P<fin>\d{1,2}/\d{1,2}/\d{2,4})"
)
# "BOSTONS GRAN PLAZA, MEXICO #6001            PAGE:   1"
RE_ENCABEZADO = re.compile(r"^(?P<nombre>.+?)\s*#(?P<id>\d{3,6})\s+PAGE:\s*\d+\s*$")

LINEAS_IGNORADAS = (
    "REPORT DATE:",
    "Menu Item Food Cost Analysis",
    "For the period:",
    "Menu Item ",
    "Inv# Name",
    "Category Totals",
    "Grand Total",
)


# ---------------------------------------------------------------------------
# Estructuras de datos
# ---------------------------------------------------------------------------


@dataclass
class ItemMenu:
    """Un renglon de producto del reporte."""

    inv: int
    nombre: str
    categoria: str
    subcategoria: str
    precio_menu: float
    num_vendidos: float
    num_eliminados: float
    ventas: float
    pct_ventas_totales: float
    costo_unitario_prom: float
    costo_total: float
    pct_costo: float
    pct_margen_contribucion: float
    utilidad: float

    @property
    def unidades_vendidas(self) -> int:
        """#Sold como entero (el reporte lo imprime con decimales)."""
        return int(round(self.num_vendidos))


@dataclass
class ReporteMenu:
    """Contenido completo de un archivo de reporte."""

    ruta: Path
    restaurante_id: str | None
    restaurante_encabezado: str | None
    fecha_inicio: date | None
    fecha_fin: date | None
    items: list[ItemMenu] = field(default_factory=list)
    _indice: dict[int, list[ItemMenu]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._reconstruir_indice()

    def _reconstruir_indice(self) -> None:
        self._indice = {}
        for item in self.items:
            self._indice.setdefault(item.inv, []).append(item)

    @property
    def periodo_reporte(self) -> str:
        """Periodo tal y como viene *dentro* del documento (ej. '3-6')."""
        if self.fecha_inicio and self.fecha_fin:
            return f"{self.fecha_inicio.day}-{self.fecha_fin.day}"
        return ""

    def buscar_por_numero(self, inv: int) -> list[ItemMenu]:
        """Todos los renglones con ese numero de item (normalmente uno)."""
        return list(self._indice.get(inv, []))

    def buscar_por_nombre(self, texto: str) -> list[ItemMenu]:
        """Items cuyo nombre contiene ``texto`` (sin distinguir mayusculas)."""
        texto = texto.strip().upper()
        return [item for item in self.items if texto in item.nombre.upper()]


# ---------------------------------------------------------------------------
# Utilidades de conversion
# ---------------------------------------------------------------------------


def _a_numero(texto: str) -> float:
    """Convierte '  33865.87', '5.43%' o '-1,435.28' en float. Vacio -> 0.0."""
    limpio = texto.strip().replace("%", "").replace(",", "").replace("$", "")
    if not limpio or limpio in {"-", "."}:
        return 0.0
    try:
        return float(limpio)
    except ValueError:
        return 0.0


def _a_fecha(texto: str) -> date | None:
    """Convierte '8/3/26' (mes/dia/anio, formato del reporte) en date."""
    partes = texto.strip().split("/")
    if len(partes) != 3:
        return None
    try:
        mes, dia, anio = (int(p) for p in partes)
    except ValueError:
        return None
    if anio < 100:
        anio += 2000
    try:
        return date(anio, mes, dia)
    except ValueError:
        return None


def _leer_texto(ruta: Path) -> str:
    """Lee el archivo probando las codificaciones tipicas de estos reportes."""
    datos = Path(ruta).read_bytes()
    for codificacion in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return datos.decode("latin-1", errors="replace")


def _campo(linea: str, nombre: str) -> str:
    inicio, fin = COLUMNAS[nombre]
    return linea[inicio:fin]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def leer_reporte(ruta: str | Path) -> ReporteMenu:
    """Lee un archivo .txt de reporte y devuelve su contenido estructurado."""
    ruta = Path(ruta)
    texto = _leer_texto(ruta)

    restaurante_id: str | None = None
    restaurante_encabezado: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    categoria = ""
    subcategoria = ""
    items: list[ItemMenu] = []

    for linea_cruda in texto.splitlines():
        linea = linea_cruda.rstrip("\r").rstrip()
        if not linea.strip():
            continue

        # Encabezado de pagina: nombre del restaurante y su #ID.
        encabezado = RE_ENCABEZADO.match(linea)
        if encabezado:
            if restaurante_id is None:
                restaurante_id = encabezado.group("id")
                restaurante_encabezado = encabezado.group("nombre").strip()
            continue

        if fecha_inicio is None:
            periodo = RE_PERIODO.search(linea)
            if periodo:
                fecha_inicio = _a_fecha(periodo.group("inicio"))
                fecha_fin = _a_fecha(periodo.group("fin"))
                continue

        if set(linea.strip()) == {"-"}:  # separadores del encabezado
            continue
        if any(marca in linea for marca in LINEAS_IGNORADAS):
            continue
        if linea.lstrip().startswith(("Subtotal", "Total")):
            continue

        # Categoria / subcategoria: la sangria distingue el nivel.
        grupo = RE_GRUPO.match(linea)
        if grupo and not RE_ITEM.match(linea):
            etiqueta = f"{grupo.group('numero')}--{grupo.group('nombre')}"
            if grupo.start("guiones") <= COLUMNA_GUIONES_CATEGORIA:
                categoria = etiqueta
                subcategoria = ""
            else:
                subcategoria = etiqueta
            continue

        if not RE_ITEM.match(linea):
            continue

        # Renglon de producto: se corta por posiciones fijas.
        linea = linea.ljust(COLUMNAS["utilidad"][1])
        try:
            inv = int(_campo(linea, "inv").strip())
        except ValueError:
            continue

        items.append(
            ItemMenu(
                inv=inv,
                nombre=_campo(linea, "nombre").strip(),
                categoria=categoria,
                subcategoria=subcategoria,
                precio_menu=_a_numero(_campo(linea, "precio_menu")),
                num_vendidos=_a_numero(_campo(linea, "num_vendidos")),
                num_eliminados=_a_numero(_campo(linea, "num_eliminados")),
                ventas=_a_numero(_campo(linea, "ventas")),
                pct_ventas_totales=_a_numero(_campo(linea, "pct_ventas_totales")),
                costo_unitario_prom=_a_numero(_campo(linea, "costo_unitario_prom")),
                costo_total=_a_numero(_campo(linea, "costo_total")),
                pct_costo=_a_numero(_campo(linea, "pct_costo")),
                pct_margen_contribucion=_a_numero(_campo(linea, "pct_margen_contribucion")),
                utilidad=_a_numero(_campo(linea, "utilidad")),
            )
        )

    return ReporteMenu(
        ruta=ruta,
        restaurante_id=restaurante_id,
        restaurante_encabezado=restaurante_encabezado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        items=items,
    )
