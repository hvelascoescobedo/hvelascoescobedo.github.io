@echo off
REM Lanzador para Windows. No contiene el programa: ejecuta generador_qry.py,
REM que debe estar en esta misma carpeta.
cd /d "%~dp0"

if not exist "generador_qry.py" (
    echo No encontre 'generador_qry.py' en esta carpeta:
    echo    %~dp0
    echo.
    echo El lanzador y el programa tienen que estar juntos en la misma carpeta.
    echo Si acabas de descomprimir una version nueva, revisa que no estes
    echo abriendo el lanzador de una carpeta vieja.
    pause
    exit /b 1
)

py -3 generador_qry.py 2>nul || python generador_qry.py
echo.
pause
