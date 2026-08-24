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
pip install -r sistema/requirements.txt
```

Al abrir la carpeta del programa solo se ven tres cosas: el ejecutable
`buscar_items.py`, la carpeta `datos/` (donde pones los reportes) y la carpeta
`resultados/` (donde salen los Excel). Todo lo demás vive dentro de `sistema/`
y no hay que tocarlo.

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

* Los **primeros 4 dígitos** son el número de restaurante (si el nombre no los
  trae, se toma el del encabezado del reporte: `BOSTONS GRAN PLAZA, MEXICO #6001`).
* **Las fechas del periodo se leen siempre de DENTRO del reporte**
  (`For the period: 8/3/26 to 8/6/26`), nunca del nombre del archivo. Lo que
  vaya entre paréntesis solo se usa para avisarte si un archivo quedó mal
  nombrado al descargarlo (ese aviso sale en pantalla y en la hoja `Archivos`).
* Da igual cómo escribas el periodo en el nombre: `6001_3-6.txt`,
  `6001-10-13.txt`, `6001 (3 al 6).txt` o `6001 (Ago 10-13).txt`.
* Las subcarpetas también se revisan, así que puedes tener una carpeta por
  periodo si así lo prefieres.

El archivo `Diccionario_restaurantes.xlsx` (el que traduce `6001` → `Merida`)
ya viene dentro de `sistema/` y se busca solo; también funciona si lo dejas
junto a los reportes.

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
Archivos leidos: 24 | restaurantes: 12 | periodos (segun el reporte): 03/08/2026-06/08/2026, 10/08/2026-13/08/2026

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

La ruta de la carpeta se puede pegar **con o sin comillas**, como venga de
Windows:

```
Carpeta con los archivos .txt de los reportes [datos]: "C:\Users\velascoh\Desktop\Hora Bostons"
Carpeta con los archivos .txt de los reportes [datos]: C:\Users\velascoh\Desktop\Hora Bostons
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

Primero van las hojas de producto × periodo y al final las tres hojas
generales: `Resultados`, `Resumen` y `Archivos`.

**Hoja `Resultados`** — todo junto, un renglón por item / restaurante / periodo:

| #ID Restaurante | Restaurante | # Item | Ventas (unidades) | Fecha inicio | Fecha fin | Nombre del item | Categoria | Subcategoria | Ventas ($) | Precio de menu | Costo total | Utilidad | Busqueda | Encontrado | Archivo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6001 | Merida | 37014 | 98 | 03/08/2026 | 06/08/2026 | PLATO DE EQUIPO | 1--STARTERS | 1--TEAM PLATTER | 33865.87 | 399.00 | 12766.63 | 21099.24 | 37014 | Si | 6001 (3-6).txt |

Las primeras cuatro columnas son justo lo pedido, y las fechas salen del propio
reporte; el resto es contexto extra que se puede ocultar o borrar. Cuando un
item no aparece en un restaurante se
incluye igual con **0 ventas** y `Encontrado = No`, para que la tabla quede
completa (con `--sin-vacios` se omiten esos renglones).

**Una hoja por cada producto y cada periodo** (van al principio del archivo) —
si buscas 2 productos y hay 2 periodos, salen 4 hojas: `37014 03-08 a 06-08`,
`37014 10-08 a 13-08`, `37021 03-08 a 06-08`, `37021 10-08 a 13-08`. Y así para
los productos y periodos que sean. Estas hojas llegan **hasta la columna
`Ventas ($)`** (las demás columnas solo están en `Resultados`):

```
Item 37014 - PLATO DE EQUIPO  |  del 03/08/2026 al 06/08/2026
#ID Restaurante | Restaurante         | # Item | Nombre del item | Ventas (unidades) | Ventas ($)
6001            | Merida              | 37014  | PLATO DE EQUIPO | 82                | 33865.87
6002            | Altabrisa           | 37014  | PLATO DE EQUIPO | 120               | 33865.87
6013            | Playa del Carmen    | 37014  | PLATO DE EQUIPO | 10                | 33865.87
6016            | Cancun              | 37014  | PLATO DE EQUIPO |                   |
6027            | Cumbres             | 37014  | PLATO DE EQUIPO |                   |
6026            | Riviera Veracruzana | 37014  | PLATO DE EQUIPO |                   |
6028            | Riviera Maya        | 37014  | PLATO DE EQUIPO |                   |
6029            | Galerias Queretaro  | 37014  | PLATO DE EQUIPO |                   |
6030            | Prime center        | 37014  | PLATO DE EQUIPO |                   |
TOTAL           |                     |        |                 | =SUMA(E3:E12)     | =SUMA(F3:F12)
```

Si buscas por nombre (`alitas`), cada hoja junta todos los productos que
coinciden en ese periodo. Por seguridad se arman como máximo 150 hojas: si
pides un rango enorme te avisa en pantalla, y la hoja `Resultados` de todos
modos trae todo.

### Los restaurantes de Oracle

Los restaurantes que no están en POSI sino en Oracle no se pueden leer de los
`.txt`, así que cada hoja los deja **ya rotulados** (número de restaurante,
nombre y el item), con el mismo formato que los demás renglones y las celdas de
ventas vacías para que las llenes a mano. El renglón `TOTAL` está hecho con
fórmula, así que **se actualiza solo** conforme capturas.

Los seis que vienen configurados son 6016 Cancun, 6027 Cumbres, 6026 Riviera
Veracruzana, 6028 Riviera Maya, 6029 Galerias Queretaro y 6030 Prime center.
Para agregar o quitar alguno se edita la lista de
`sistema/analizador/configuracion.py`:

```python
RESTAURANTES_ORACLE: list[tuple[str, str]] = [
    ("6016", "Cancun"),
    ("6027", "Cumbres"),
    ...
]
```

Si algún día uno de ellos empieza a aparecer en los reportes, el programa lo
detecta y ya no lo repite como renglón para capturar.

**Hoja `Resumen`** — totales por item y periodo (fecha inicio / fecha fin): en
cuántos restaurantes se vendió, unidades e importe.

**Hoja `Archivos`** — el registro de cada archivo leído: qué restaurante se
dedujo, las fechas que venían dentro del reporte, cuántos items se leyeron, si
hubo algún problema y un **aviso** cuando el periodo del nombre del archivo no
coincide con las fechas del reporte.

### ¿Por qué hay ventas en negativo?

Porque así vienen en el reporte. Los items de la categoría
`20--APPROVED PROMO` (y algunos modificadores como `DELIVERY` o los combos de
niños) son **promociones, descuentos y cortesías**: el sistema registra el
importe que se descontó de la venta, por eso aparece con signo menos. Las
unidades siguen siendo positivas, porque son las veces que se aplicó la promo.

```
   10258 BONELESS <SPECIA   249.00      94.00       0.00  -10534.57   -1.69% ...
                                                          ^ tal cual en el .txt
```

En el reporte del ejemplo son 24 items de 712, y sus importes suman
-46,845.49 contra 670,634.93 de venta positiva; la resta da los 623,789.50 del
renglón `Category Totals`. El programa no cambia esos signos: si los volviera
positivos, los totales dejarían de cuadrar con el reporte. Cuando buscas uno de
esos items, la terminal te lo avisa y en la hoja `Resultados` puedes ver su
categoría.

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
├── buscar_items.py              <- lo único que se ejecuta
├── datos/                       <- aquí van los .txt descargados
├── resultados/                  <- aquí se guardan los Excel generados
└── sistema/                     (el motor: no hace falta abrirlo)
    ├── analizador/
    │   ├── parser_reporte.py    lectura de los .txt de ancho fijo
    │   ├── nombre_archivo.py    "6001 (3-6).txt" -> número de restaurante
    │   ├── diccionario.py       Excel de restaurantes (#ID -> nombre)
    │   ├── busqueda.py          búsqueda de items en todos los archivos
    │   ├── exportar_excel.py    generación del Excel de resultados
    │   └── configuracion.py     lista de restaurantes de Oracle
    ├── tests/                   pruebas automáticas
    ├── Diccionario_restaurantes.xlsx
    ├── requirements.txt
    └── README.md                este archivo
```

## 7. Pruebas

```bash
cd sistema
python -m unittest discover tests
```
