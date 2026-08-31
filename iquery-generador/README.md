# Generador de consultas .qry para iQuery  (versión 4.0)

Genera archivos `.qry` del subject **Discount Daily Total** listos para abrirse en
iQuery. El subject, las columnas, el orden y el filtro de sucursales se quedan
**exactamente igual** que en la consulta original; lo único que cambia en cada
archivo son los **productos** consultados (`discNum`).

> **Sobre las fechas:** iQuery ignora el rango de fechas que trae el archivo y lo
> reemplaza por el día de hoy, así que el programa ya no te lo pregunta. El
> periodo se ajusta **dentro de iQuery**, al abrir la consulta. El `.qry` sí
> conserva el filtro de fechas (con la fecha de hoy) nada más para mantener la
> misma estructura que exporta iQuery; si alguna vez quieres generarlo sin ese
> filtro, pon `INCLUIR_FILTRO_FECHAS = False` arriba de `generador_qry.py`.

## Cómo se usa

| Sistema | Qué hacer |
|---|---|
| macOS | Doble clic en `generar_qry.command` (o en la Terminal: `./generar_qry.sh`) |
| Linux | `./generar_qry.sh` |
| Windows | Doble clic en `generar_qry.bat` (o `bash generar_qry.sh` en Git Bash) |

Si prefieres correrlo directo: `python3 generador_qry.py`

> La primera vez en macOS/Linux, si el doble clic no funciona, dale permisos con:
> `chmod +x generar_qry.sh generar_qry.command`

### ¿Estoy corriendo la versión nueva?

Los tres lanzadores (`.sh`, `.command`, `.bat`) **no contienen el programa**: solo
buscan Python y ejecutan el `generador_qry.py` que esté **en su misma carpeta**.
Todos los mensajes y preguntas viven en el `.py`.

Por eso, al actualizar, reemplaza la carpeta completa. Si descomprimes el zip
nuevo junto al viejo, el sistema crea `iquery-generador 2` y, si abres el
lanzador de la carpeta vieja, seguirás viendo la versión anterior.

Para saber cuál estás corriendo, mira la primera línea al abrirlo:

```
  GENERADOR DE CONSULTAS .qry PARA iQuery   (versión 4.0)
  Carpeta destino: /ruta/de/la/carpeta/que/se/esta/usando/codigos
```

Si el `.py` no está junto al lanzador, este te lo avisa en vez de fallar.

### Nota para Windows

`generar_qry.bat` pone la consola en UTF-8 (`chcp 65001`) antes de arrancar,
porque `cmd.exe` normalmente usa cp850/cp437 y ahí los acentos y la palomita
no existen. Además el programa ya no truena si la consola no soporta algún
carácter: lo reemplaza y sigue. Si la consola no soporta los recuadros, los
dibuja con `=`, `-` y `|`.

Si Windows no encuentra Python, el `.bat` te lo dice y te deja la ventana
abierta con el mensaje (antes solo parpadeaba y se cerraba).

## Qué te va a preguntar

Cada consulta son 2 pasos. Todas las preguntas dicen exactamente qué escribir,
y las de sí/no se contestan con **`s`** o **`n`**.

**Paso 1 · Productos** — uno por línea, o varios de un jalón separados por coma
o espacio (`207, 206, 310`). Enter en blanco para terminar. Cada producto se
agrega como un filtro `EQUAL … OR`, igual que en la consulta original.

```
  [ PASO 1 de 2 ]   PRODUCTOS (discNum)

      Producto #1 (escribe el discNum): 207, 206
      -> En la lista: 207, 206
      Producto #3 (escribe el discNum):
```

**Paso 2 · Dónde guardarlo** — te enseña las carpetas que ya existen y eliges
si guardas en una de ellas o creas una nueva.

```
  [ PASO 2 de 2 ]   DÓNDE GUARDAR EL ARCHIVO

    Carpetas que ya existen dentro de 'codigos':

        1)  Hora Bostons            (2 archivos .qry)
        2)  Mes Patrio              (1 archivo .qry)

    ¿Qué quieres hacer?

        1)  Guardar en una de las carpetas de arriba
        2)  Crear una carpeta nueva

      Opción (escribe 1 o 2): 1
      Carpeta (escribe el número de la carpeta, 1-2): 1
      -> Se guardará en: codigos/Hora Bostons/
```

Al terminar te muestra el resumen del archivo y pregunta si sigues:

```
  ┌─ ✔ ARCHIVO GENERADO
  │
  │   Archivo    :  207-206.qry
  │   Carpeta    :  codigos/Hora Bostons
  │   Productos  :  207, 206
  │
  └───────────────────────────────────────────────────────────────

      ¿Quieres hacer otra consulta? (s / n): n
```

Con `s` empieza otra consulta; con `n` cierra el programa y te da la lista de
todo lo que generó. A partir de la segunda consulta te pregunta si quieres
**reusar** los productos o la carpeta de la anterior.

## Dónde quedan los archivos

```
iquery-generador/
├── generador_qry.py
├── generar_qry.sh / .command / .bat
└── codigos/
    ├── Hora Bostons/
    │   ├── 207-206.qry
    │   └── 310.qry
    └── Mes Patrio/
        └── 207.qry
```

Formato del nombre: **solo el discNum**. Si son varios, se unen con guion:
`207-206.qry`.

Si en esa carpeta ya existe un archivo con ese nombre te pregunta si lo
reemplazas; si dices que `n`, lo guarda como `207-206 (2).qry`.

## Si necesitas cambiar algo fijo

Todo lo "fijo" está en las constantes de hasta arriba de `generador_qry.py`:

| Constante | Para qué sirve |
|---|---|
| `SUBJECT`, `COLUMNAS`, `ORDENES` | El reporte y sus columnas |
| `SUCURSALES` | Los IDs de las sucursales del filtro `locName` |
| `VERSION_PROGRAMA`, `VERSION_METADATA` | Versiones que escribe iQuery |
| `INCLUIR_FILTRO_FECHAS` | Si el .qry lleva o no el filtro de fechas |

## Detalles técnicos

* Solo necesita **Python 3** (sin librerías externas).
* El `.qry` se escribe con saltos de línea de Windows (CRLF) y el JSON compacto,
  byte por byte igual al que exporta iQuery.
