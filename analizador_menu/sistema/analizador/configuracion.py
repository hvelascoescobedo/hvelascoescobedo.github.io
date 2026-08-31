"""Ajustes que se editan a mano.

Aqui esta la lista de restaurantes que NO usan POSI sino Oracle: como sus
reportes no se descargan igual, el programa no puede leerlos, asi que en cada
hoja de producto x periodo deja sus renglones ya rotulados (numero y nombre del
restaurante) para capturar las ventas a mano.

Para agregar o quitar un restaurante de Oracle basta con editar esta lista.
"""

from __future__ import annotations

# (numero de restaurante, nombre).  Aparecen en la hoja ordenados por numero,
# sin importar en que orden se escriban aqui.
RESTAURANTES_ORACLE: list[tuple[str, str]] = [
    ("6016", "Cancun"),
    ("6026", "Riviera Veracruzana"),
    ("6027", "Cumbres"),
    ("6028", "Riviera Maya"),
    ("6029", "Galerias Queretaro"),
    ("6030", "Prime center"),
]
