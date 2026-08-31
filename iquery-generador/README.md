# Generador de consultas .qry para iQuery

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

## Qué te va a preguntar

1. **Fecha de inicio**: primero el **día**, luego el **mes** (1 = enero … 12 = diciembre)
   y luego el **año**. Lo mismo para la **fecha de fin**.
   Valida días imposibles (31 de febrero) y que el fin no sea anterior al inicio.
2. **Productos**: escribe un `discNum` por línea, o varios de un jalón separados por
   coma o espacio (`207, 206, 310`). Enter en blanco para terminar.
   Cada producto se agrega como un filtro `EQUAL … OR`, igual que en la consulta original.
3. **Dónde guardarlo**:
   * *Carpeta existente* → te muestra la lista numerada de lo que hay dentro de `codigos/`
     y eliges por número.
   * *Carpeta nueva* → le pones nombre (ej. `Hora Bostons`) y se crea sola.
4. **¿Generar otra consulta?** → puedes hacer todas las que quieras en una sola corrida.
   A partir de la segunda te ofrece **reusar** fechas, productos o carpeta, para cuando
   solo cambia una de las tres cosas.

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

Si un archivo ya existe te pregunta si lo sobrescribes; si dices que no, lo guarda
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
