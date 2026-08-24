"""Interpretacion de los nombres de archivo descargados de cada restaurante.

Del nombre se toma el **numero de restaurante**.  El periodo tambien se
interpreta, pero solo para avisar si el archivo quedo mal nombrado: las fechas
buenas son siempre las que vienen dentro del reporte.

Los archivos se descargan uno por restaurante y por periodo, con nombres del
estilo::

    6001 (3-6).txt      -> restaurante 6001, periodo "3-6"
    6002 (10-13).txt    -> restaurante 6002, periodo "10-13"

Se aceptan tambien variantes frecuentes al renombrar o al descargar::

    6001_3-6.txt, 6001-3-6.txt, 6001 3-6.txt, 6001 (3 al 6).txt,
    6001 (Ago 3-6).txt, 6001.txt (sin periodo: se toma del contenido)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# 4 digitos al inicio = numero de restaurante.
RE_ID = re.compile(r"^\s*(?P<id>\d{4})(?!\d)")
# Periodo entre parentesis o corchetes: "(3-6)", "[10-13]".
RE_PERIODO_PARENTESIS = re.compile(r"[\(\[](?P<periodo>[^\)\]]+)[\)\]]")
# Periodo pegado al ID: "6001_3-6", "6001-10-13", "6001 3-6".
RE_PERIODO_SUELTO = re.compile(r"^\s*\d{4}\s*[ _\-.]+(?P<periodo>.+?)\s*$")
# Dias dentro de la etiqueta del periodo: "3-6", "3 al 6", "Ago 3-6".
RE_DIAS = re.compile(r"(?P<inicio>\d{1,2})\s*(?:-|a|al|to|~)\s*(?P<fin>\d{1,2})", re.IGNORECASE)

EXTENSIONES_VALIDAS = {".txt", ".prn", ".rpt", ".dat", ".text"}


@dataclass
class InfoArchivo:
    """Datos deducidos del nombre del archivo."""

    ruta: Path
    restaurante_id: str | None
    periodo: str | None
    dia_inicio: int | None = None
    dia_fin: int | None = None

    @property
    def nombre_archivo(self) -> str:
        return self.ruta.name

    @property
    def periodo_normalizado(self) -> str:
        """Periodo en formato homogeneo 'inicio-fin' cuando se pudo deducir."""
        if self.dia_inicio is not None and self.dia_fin is not None:
            return f"{self.dia_inicio}-{self.dia_fin}"
        return self.periodo or ""


def interpretar_nombre(ruta: str | Path) -> InfoArchivo:
    """Deduce el #ID de restaurante y el periodo a partir del nombre."""
    ruta = Path(ruta)
    base = ruta.stem.strip()

    coincidencia_id = RE_ID.match(base)
    restaurante_id = coincidencia_id.group("id") if coincidencia_id else None

    periodo: str | None = None
    entre_parentesis = RE_PERIODO_PARENTESIS.search(base)
    if entre_parentesis:
        periodo = entre_parentesis.group("periodo").strip()
    else:
        suelto = RE_PERIODO_SUELTO.match(base)
        if suelto:
            periodo = suelto.group("periodo").strip()

    dia_inicio = dia_fin = None
    if periodo:
        dias = RE_DIAS.search(periodo)
        if dias:
            dia_inicio = int(dias.group("inicio"))
            dia_fin = int(dias.group("fin"))

    return InfoArchivo(
        ruta=ruta,
        restaurante_id=restaurante_id,
        periodo=periodo,
        dia_inicio=dia_inicio,
        dia_fin=dia_fin,
    )


def listar_archivos(carpeta: str | Path, recursivo: bool = True) -> list[Path]:
    """Devuelve todos los reportes de la carpeta, ordenados por nombre.

    No hace falta indicar los archivos uno por uno: se toman todos los que
    tengan una extension de texto valida (22 restaurantes x N periodos).
    """
    carpeta = Path(carpeta)
    if not carpeta.exists():
        raise FileNotFoundError(f"No existe la carpeta: {carpeta}")
    if not carpeta.is_dir():
        raise NotADirectoryError(f"No es una carpeta: {carpeta}")

    patron = "**/*" if recursivo else "*"
    archivos = [
        p
        for p in carpeta.glob(patron)
        if p.is_file()
        and p.suffix.lower() in EXTENSIONES_VALIDAS
        and not p.name.startswith((".", "~$"))
    ]
    return sorted(archivos, key=lambda p: (p.parent.as_posix(), p.name))
