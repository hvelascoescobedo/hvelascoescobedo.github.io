# Analizador de ventas por item (reportes de restaurantes)

Herramienta en Python para buscar **cuántas ventas tuvo un producto** en los
reportes *Menu Item Food Cost Analysis* que se descargan de la computadora de
cada restaurante, y entregar el resultado en un **archivo de Excel**.

El programa lee **todos** los archivos de una carpeta (no hay que indicarlos uno
por uno), sin importar si son 24, 66 o los que sean: reconoce el número de
restaurante y el periodo desde el nombre del archivo.

---

## 1. Instalación (una sola vez)

Se necesita Python 3.10 o superior.

```bash
cd analizador_menu
pip install -r requirements.txt
```

## 2. Preparar la carpeta

Coloca los `.txt` descargados dentro de `datos/` (o de cualquier carpeta que
prefieras), con la forma de siempre:

```
datos/
├── 6001 (3-6).txt        ← restaurante 6001, del 3 al 6 de agosto
├── 6001 (10-13).txt      ← restaurante 6001, del 10 al 13 de agosto
├── 6002 (3-6).txt
├── 6002 (10-13).txt
└── ...
```

* Los **primeros 4 dígitos** son el número de restaurante.
* Lo que va **entre paréntesis** es el periodo.
* También se aceptan variantes como `6001_3-6.txt`, `6001-10-13.txt`,
  `6001 (3 al 6).txt` o `6001 (Ago 10-13).txt`.
* Si el nombre no trae periodo, se toma el que viene **dentro** del reporte
  (`For the period: 8/3/26 to 8/6/26`), y lo mismo pasa con el número de
  restaurante (`BOSTONS GRAN PLAZA, MEXICO #6001`).
* Las subcarpetas también se revisan, así que puedes tener una carpeta por
  periodo si así lo prefieres.

El archivo `Diccionario_restaurantes.xlsx` (el que traduce `6001` → `Merida`)
se busca solo: basta con dejarlo en esta carpeta o junto a los reportes.

## 3. Usarlo

### Modo interactivo (el programa pregunta todo)

```bash
python buscar_items.py
```

```
Carpeta con los archivos .txt de los reportes [datos]:
Diccionario de restaurantes: 28 restaurantes cargados

Leyendo archivos...
  [  1/24] 6001 (3-6).txt
  ...
Archivos leidos: 24 | restaurantes: 12 | periodos: 10-13, 3-6

Item(s) a buscar: 37014, 37021
```

Se puede buscar:

| Lo que escribes | Lo que hace |
| --- | --- |
| `37014` | un item |
| `37014, 37021, 37031` | varios items a la vez |
| `37014-37020` | todo un rango de números |
| `alitas` | busca por **nombre** del producto (todos los que lo contengan) |

Al terminar pregunta el nombre del Excel y ofrece hacer otra búsqueda sin
volver a leer los archivos.

### Modo directo (sin preguntas, para automatizar)

```bash
python buscar_items.py --carpeta datos --items 37014,37021 --salida ventas_agosto.xlsx
```

| Opción | Para qué sirve |
| --- | --- |
| `--carpeta` | carpeta con los reportes (por defecto `datos`) |
| `--items` | items a buscar, separados por comas |
| `--salida` | nombre del Excel de resultados |
| `--diccionario` | ruta del `Diccionario_restaurantes.xlsx` |
| `--sin-vacios` | no incluir los restaurantes donde el item no aparece |
| `--no-recursivo` | leer solo esa carpeta, sin entrar a las subcarpetas |

Los resultados se guardan en `resultados/` cuando no se da una ruta completa.

## 4. Qué contiene el Excel

**Hoja `Resultados`** — un renglón por item / restaurante / periodo:

| #ID Restaurante | Restaurante | # Item | Ventas (unidades) | Periodo | Fecha inicio | Fecha fin | Nombre del item | Categoria | Subcategoria | Ventas ($) | Precio de menu | Costo total | Utilidad | Busqueda | Encontrado | Archivo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6001 | Merida | 37014 | 98 | 3-6 | 03/08/2026 | 06/08/2026 | PLATO DE EQUIPO | 1--STARTERS | 1--TEAM PLATTER | 33865.87 | 399.00 | 12766.63 | 21099.24 | 37014 | Si | 6001 (3-6).txt |

Las primeras cuatro columnas son justo lo pedido; el resto es contexto extra que
se puede ocultar o borrar. Cuando un item no aparece en un restaurante se
incluye igual con **0 ventas** y `Encontrado = No`, para que la tabla quede
completa (con `--sin-vacios` se omiten esos renglones).

**Hoja `Resumen`** — totales por item y periodo: en cuántos restaurantes se
vendió, unidades e importe.

**Hoja `Archivos`** — el registro de cada archivo leído: qué restaurante y qué
periodo se dedujeron del nombre, las fechas que venían dentro del reporte,
cuántos items se leyeron y si hubo algún problema.

## 5. Cómo se lee el reporte

Los `.txt` vienen paginados (cada página repite el encabezado), pero todas las
páginas tienen las mismas columnas de ancho fijo:

```
   37014 PLATO DE EQUIPO    399.00      98.00       0.00   33865.87    5.43%     130.2717   12766.63   37.6976%    5.09%   21099.24
   └─Inv#└─Name             └─Price     └─#Sold     └─#Del └─Sales     └─%Tot    └─UnitCost └─Cost     └─Cost%     └─Margin └─Profit
```

El parser (`analizador/parser_reporte.py`) recorta por posición de columna, se
salta encabezados de página, subtotales y totales, y arrastra la **categoría**
(` 1--STARTERS`) y la **subcategoría** (`   1--TEAM PLATTER`) hacia cada item.
Ojo con un detalle del formato: los números de grupo van alineados a la derecha,
así que `10--EXTRA TOPPINGS` es categoría y `  10--OPEN LIQUOR` es subcategoría;
lo que distingue el nivel es la columna donde empiezan los guiones.

Como verificación, la suma de `#Sold` de todos los items leídos coincide
exactamente con el renglón `Category Totals` del propio reporte, y cada
`Subtotal` de categoría coincide con la suma de sus items (se comprueba en las
pruebas).

## 6. Estructura del proyecto

```
analizador_menu/
├── buscar_items.py              programa principal (interactivo y por terminal)
├── analizador/
│   ├── parser_reporte.py        lectura de los .txt de ancho fijo
│   ├── nombre_archivo.py        "6001 (3-6).txt" -> restaurante + periodo
│   ├── diccionario.py           Excel de restaurantes (#ID -> nombre)
│   ├── busqueda.py              búsqueda de items en todos los archivos
│   └── exportar_excel.py        generación del Excel de resultados
├── datos/                       aquí van los .txt descargados
├── resultados/                  aquí se guardan los Excel generados
├── tests/                       pruebas automáticas
├── Diccionario_restaurantes.xlsx
└── requirements.txt
```

## 7. Pruebas

```bash
python -m unittest discover tests
```
