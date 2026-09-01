# Generador de reportes REPORTSW

Convierte fechas normales (`dd/mm/aaaa`) en los números "hace cuántos días"
que necesita la línea `REPORTSW` de PosiTouch, y escribe un `.BAT` nuevo ya
configurado.

```
REPORTSW 8 C 15 13 N 4 YYYYYYYYYYYYYYYYYYYYY N Y 1 N N
                ^  ^
                |  +-- fin    = hace 13 días
                +----- inicio = hace 15 días
```

## Cómo se usa

1. Doble clic en **`Generar reporte.bat`**.
2. Escribe la fecha de inicio y la de fin (`15/08/2026`, o `15-08-2026`, o
   atajos como `hoy` / `ayer` / `anteayer`).
3. El programa toma la fecha de hoy del reloj de la computadora, calcula los
   días y guarda el `.BAT` en la carpeta **`ejeutables`**.
4. Pregunta si quieres generar otro. Puedes repetir las veces que quieras;
   escribe `salir` en cualquier fecha para terminar.

Ejemplo, ejecutado el 01/09/2026:

| Escribes            | Se calcula            | Línea generada          | Archivo                        |
|---------------------|-----------------------|-------------------------|--------------------------------|
| 15/08/2026 → 17/08/2026 | hace 17 → hace 15 días | `REPORTSW 8 C 17 15 ...` | `ejeutables/15-08-26 a 17-08-26.bat` |

## Archivos

| Archivo                  | Para qué sirve |
|--------------------------|----------------|
| `Generar reporte.bat`    | Lo que se abre con doble clic. Busca Python (`py` o `python`) y lanza el script. |
| `generador_reportes.py`  | El programa. |
| `plantilla.BAT`          | El `.BAT` original. Se copia tal cual y sólo se le cambian los dos números. |
| `ejeutables/`            | Aquí se guardan los `.BAT` generados. |

## Cosas importantes

- **Los `.BAT` generados caducan.** Los números son "días desde hoy", así que
  un archivo generado hoy sólo da el periodo correcto si se ejecuta hoy. Cada
  archivo lleva arriba un comentario `REM` con la fecha en que se generó.
- **El nombre lleva `a` en vez de `/`.** Windows no permite `/` en nombres de
  archivo, así que `15/08/26 // 17/08/26` se guarda como
  `15-08-26 a 17-08-26.bat`. Para cambiar el separador, edita
  `SEPARADOR_NOMBRE` arriba del `.py`.
- **Si cambias el reporte** (otro tipo, otras opciones), edita
  `plantilla.BAT` con la configuración que quieras. Sólo tiene que conservar
  una línea con el formato `REPORTSW <algo> <algo> <número> <número> ...`;
  todo lo demás se copia sin tocarse.
- **La carpeta se llama `ejeutables`** tal como se pidió. Si prefieres
  `ejecutables`, cambia `CARPETA_SALIDA` arriba del `.py`.

## Requisitos

Python 3 instalado en la computadora, con la opción *"Add Python to PATH"*
marcada durante la instalación (https://www.python.org/downloads/).
