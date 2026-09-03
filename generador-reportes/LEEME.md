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
  generar antes de que se sobrescriba con el siguiente. Si contestas `S`
  sigue con el próximo; si contestas `N`, el `.BAT` se cierra ahí mismo sin
  correr los reportes que faltaban.

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
- **`choice` necesita Windows Vista o más nuevo** (7/10/11 lo traen). Si la
  máquina de PosiTouch corre algo más viejo que eso, avísame y lo cambio por
  un `pause` simple (sin poder contestar "no" a mitad de la corrida).
- **Si cambias el reporte** (otro tipo, otras opciones), edita
  `plantilla.BAT` con la configuración que quieras. Sólo tiene que conservar
  una línea con el formato `REPORTSW <algo> <algo> <número> <número> ...`;
  todo lo demás se copia sin tocarse.
- **La carpeta se llama `ejeutables`** tal como se pidió. Si prefieres
  `ejecutables`, cambia `CARPETA_SALIDA` arriba del `.py`.

## Requisitos

Python 3 instalado en la computadora, con la opción *"Add Python to PATH"*
marcada durante la instalación (https://www.python.org/downloads/).
