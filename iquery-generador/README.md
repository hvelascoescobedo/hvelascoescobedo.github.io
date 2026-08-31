# Generador de consultas .qry para iQuery  (versión 2.1)

Genera archivos `.qry` del subject **Discount Daily Total** listos para abrirse en
iQuery. El subject, las columnas, el orden y el filtro de sucursales se quedan
**exactamente igual** que en la consulta original; lo único que cambia en cada
archivo es:

* el **rango de fechas** (`busDate`), y
* los **productos** consultados (`discNum`).

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
  GENERADOR DE CONSULTAS .qry PARA iQuery   (versión 2.1)
  Carpeta destino: /ruta/de/la/carpeta/que/se/esta/usando/codigos
```

Si el `.py` no está junto al lanzador, este te lo avisa en vez de fallar.

### Nota para Windows

`generar_qry.bat` pone la consola en UTF-8 (`chcp 65001`) antes de arrancar,
porque `cmd.exe` normalmente usa cp850/cp437 y ahí los acentos y la palomita
no existen. Además el programa ya no truena si la consola no soporta algún
carácter: lo reemplaza y sigue.

Si Windows no encuentra Python, el `.bat` te lo dice y te deja la ventana
abierta con el mensaje (antes solo parpadeaba y se cerraba).

## Qué te va a preguntar

Todas las preguntas dicen exactamente qué escribir. Las de sí/no se contestan
escribiendo `si` o `no`.

1. **Fechas** — primero la de inicio y luego la de fin, cada una en tres pasos:

   ```
   --- Fecha de INICIO ---
     Día (escribe el número del día, 1-31): 3
     Meses:
         1. Enero          2. Febrero        3. Marzo
         4. Abril          5. Mayo           6. Junio
         7. Julio          8. Agosto         9. Septiembre
        10. Octubre       11. Noviembre     12. Diciembre
     Mes (escribe el número del mes, 1-12): 8
     Año (escribe el año, ejemplo 2026): 2026
     = Fecha de inicio: 3 de Agosto de 2026
   ```

   Valida días imposibles (31 de febrero) y que el fin no sea anterior al inicio.

2. **Productos** — `discNum del producto #1:` … escribe uno por línea, o varios de
   un jalón separados por coma o espacio (`207, 206, 310`). Enter en blanco para
   terminar de agregar. Cada producto se agrega como un filtro `EQUAL … OR`, igual
   que en la consulta original.

3. **Dónde guardarlo** — `Opción (escribe 1 o 2):`
   * `1` Carpeta que ya existe → te muestra la lista numerada de lo que hay dentro
     de `codigos/` y eliges con `Carpeta (escribe el número de la carpeta):`
   * `2` Carpeta nueva → `Nombre de la nueva carpeta (ejemplo: Hora Bostons):`

4. **`¿Quieres hacer otra consulta? (escribe: si / no):`** — con `si` empieza otra
   consulta; con `no` se cierra el programa y te muestra el resumen de todo lo que
   generó. A partir de la segunda consulta te pregunta si quieres **reusar** las
   fechas, los productos o la carpeta de la anterior, para cuando solo cambia una
   de las tres cosas.

## Dónde quedan los archivos

```
iquery-generador/
├── generador_qry.py
├── generar_qry.sh / .command / .bat
└── codigos/
    ├── Hora Bostons/
    │   ├── 207-206 03-08-2026 - 06-08-2026.qry
    │   └── 310 03-08-2026 - 06-08-2026.qry
    └── Mes Patrio/
        └── 207-206 15-09-2026 - 20-09-2026.qry
```

Formato del nombre: `discNum(s) FechaInicio - FechaFin.qry`
(varios productos se unen con guion: `207-206`; fechas en `dd-mm-aaaa`).

Si un archivo ya existe te pregunta si lo reemplazas; si dices que `no`, lo guarda
como `… (2).qry`.

## Si necesitas cambiar algo fijo

Todo lo "fijo" está en las constantes de hasta arriba de `generador_qry.py`:

| Constante | Para qué sirve |
|---|---|
| `SUBJECT`, `COLUMNAS`, `ORDENES` | El reporte y sus columnas |
| `SUCURSALES` | Los IDs de las sucursales del filtro `locName` |
| `VERSION_PROGRAMA`, `VERSION_METADATA` | Versiones que escribe iQuery |
| `FORMATO_FECHA_ARCHIVO` | Formato de fecha en el nombre del archivo |

## Detalles técnicos

* Solo necesita **Python 3** (sin librerías externas).
* El `.qry` se escribe con saltos de línea de Windows (CRLF) y el JSON compacto,
  byte por byte igual al que exporta iQuery.
