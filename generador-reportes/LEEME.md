# Generador de reportes REPORTSW

Convierte fechas reales (día/mes/año) en los números "hace cuántos días"
que necesita la línea `REPORTSW` de PosiTouch, y arma **un solo `.BAT`**
con todos los reportes que le pidas en una sesión.

```
REPORTSW 8 C 15 13 N 4 YYYYYYYYYYYYYYYYYYYYY N Y 1 N N
                ^  ^
                |  +-- fin    = hace 13 días
                +----- inicio = hace 15 días
```

## Cómo se usa

1. Doble clic en **`Generar reporte.bat`**.
2. Por cada reporte que quieras, contesta seis preguntas, un dato por
   renglón y solo con números:

   ```
     Día de inicio  : 15
     Mes de inicio  : 8
     Año de inicio  : 2026

     Día de fin     : 17
     Mes de fin     : 8
     Año de fin     : 2026
   ```

   El año puede ir completo (`2026`) o de dos dígitos (`26`). Atajo: escribe
   `hoy`, `ayer` o `anteayer` en la pregunta del día y llena la fecha entera.
3. Al terminar cada reporte te pregunta **"¿Agregar otro reporte a este
   mismo archivo .BAT?"**. Contesta `s` y vuelve a pedir las seis preguntas
   para el siguiente periodo. Contesta `n` cuando ya no quieras agregar más.
4. El programa guarda **un único `.BAT`** con todos los reportes, en orden,
   en la carpeta **`ejeutables`**.
5. Al final pregunta si quieres generar **otro archivo `.BAT`** (para otro
   grupo de fechas). Puedes repetir las veces que quieras; escribe `salir`
   en cualquier pregunta para terminar del todo.

### Qué pasa cuando ejecutas el `.BAT` en la máquina de PosiTouch

- Si solo pediste **un** reporte, el `.BAT` corre directo, igual que el
  original.
- Si pediste **varios**, el `.BAT` corre el primer reporte, se detiene y
  pregunta:

  ```
    Continuar con el reporte 2 de 3 (S/N)?
  ```

  Eso te da tiempo de guardar o renombrar el reporte que se acaba de
  generar antes de que se sobrescriba con el siguiente. Presiona **`S`**
  para seguir con el próximo o **`N`** para cerrar el `.BAT` ahí mismo sin
  correr los reportes que faltaban (no hace falta Enter).

  **Antes de contestar `S`, cierra el archivo del reporte anterior** si lo
  abriste en Excel o el Bloc de notas: si sigue abierto, PosiTouch puede no
  poder escribir el siguiente.

Ejemplo, ejecutado el 03/09/2026, pidiendo 2 reportes en un mismo `.BAT`:

| Reporte | Contestas               | Se calcula             | Línea generada           |
|---------|--------------------------|-------------------------|---------------------------|
| 1       | 15/08/2026 → 17/08/2026 | hace 19 → hace 17 días | `REPORTSW 8 C 19 17 ...` |
| 2       | 20/08/2026 → 22/08/2026 | hace 14 → hace 12 días | `REPORTSW 8 C 14 12 ...` |

Archivo generado: `ejeutables/15-08-26 a 22-08-26 (2 reportes).bat`

## Archivos

| Archivo                  | Para qué sirve |
|--------------------------|----------------|
| `Generar reporte.bat`    | Lo que se abre con doble clic. Busca Python (`py` o `python`) y lanza el script. |
| `generador_reportes.py`  | El programa. |
| `plantilla.BAT`          | El `.BAT` original. El bloque `REPORTSW` se repite una vez por reporte; lo demás (`cd`, `mkdir`, etc.) se pone una sola vez al principio. |
| `ejeutables/`            | Aquí se guardan los `.BAT` generados. |

## Cosas importantes

- **Los `.BAT` generados caducan.** Los números son "días desde hoy", así que
  un archivo generado hoy sólo da los periodos correctos si se ejecuta hoy.
  El `.BAT` lleva arriba un comentario `REM` con la fecha en que se generó y
  el detalle de cada reporte que contiene.
- **El nombre usa la primera y la última fecha.** Con varios reportes en un
  mismo archivo, el nombre toma el inicio del primero y el fin del último,
  más un `(n reportes)`, por ejemplo
  `15-08-26 a 22-08-26 (2 reportes).bat`. Windows no permite `/` en nombres
  de archivo, por eso se usa ` a ` en vez de ` // `; para cambiar el
  separador, edita `SEPARADOR_NOMBRE` arriba del `.py`.
- **Si te equivocas, no pasa nada.** Un día 32, un mes 13, un 31 de febrero o
  una fecha del futuro se rechazan con un mensaje y vuelve a preguntar. Si
  pones el inicio después del fin, te ofrece invertirlas.
- **`CHOICE` se llama por su ruta completa, a propósito.** Escrito a secas
  como `choice`, Windows lo busca **primero en la carpeta actual** — que
  aquí es `C:\SC` — y ahí vive un `CHOICE` antiguo de PosiTouch que aborta
  con *"CHOICE: invalid choice switch syntax"*. Por eso el `.BAT` llama
  `%SystemRoot%\System32\choice.exe`, que siempre es el de Windows. Si
  ese archivo no existiera (Windows muy viejo), el `.BAT` se cae solo a un
  `set /p`, que es interno de `cmd.exe` y nunca falta.
- **Si cambias el reporte** (otro tipo, otras opciones), edita
  `plantilla.BAT` con la configuración que quieras. Sólo tiene que conservar
  una línea con el formato `REPORTSW <algo> <algo> <número> <número> ...`;
  todo lo demás se copia sin tocarse.
- **La carpeta se llama `ejeutables`** tal como se pidió. Si prefieres
  `ejecutables`, cambia `CARPETA_SALIDA` arriba del `.py`.

## Si algo falla al correr el `.BAT`

| Lo que ves | Qué es | Qué hacer |
|------------|--------|-----------|
| `CHOICE: invalid choice switch syntax` | El `.BAT` es de una versión vieja del generador, la que llamaba `choice` a secas. | Regenera el `.BAT` con esta versión. |
| `UTILITY ABORT — User Error ...70... Check BTREE Manual` | **No es del `.BAT`**: es PosiTouch (`REPORTSW`) abortando contra su base de datos Btrieve. El `.BAT` sólo lo llama, con los mismos parámetros de siempre y sólo cambiando los dos números. | Ver abajo. |

Para el error de BTREE, lo que ayuda a ubicarlo:

1. **¿En qué reporte falló?** Si falla en el primero, el problema no tiene
   que ver con encadenar varios: el mismo periodo falla también en un
   `.BAT` de un solo reporte. Pruébalo para confirmarlo.
2. **¿Tenías abierto el reporte anterior?** Si lo dejaste abierto en Excel
   o el Bloc de notas, `REPORTSW` puede no poder escribir el siguiente.
3. **¿El periodo incluye el día de hoy?** Algunos reportes de PosiTouch no
   pueden cerrar un día que todavía está abierto. Prueba el mismo `.BAT`
   con el periodo terminando ayer.
4. **¿Es un periodo muy viejo?** Si esos días ya fueron purgados de la base
   de datos, no hay nada que reportar y la utilería aborta.

El `.BAT` ya espera 10 segundos después de cada reporte (como el original) y
otros 5 después de que contestas `S`, para darle margen a PosiTouch a soltar
sus archivos. Ese segundo margen se cambia en `SEGUNDOS_ENTRE_REPORTES`,
arriba del `.py`.

## Requisitos

Python 3 instalado en la computadora, con la opción *"Add Python to PATH"*
marcada durante la instalación (https://www.python.org/downloads/).
