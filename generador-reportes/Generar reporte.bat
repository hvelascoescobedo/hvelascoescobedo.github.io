@echo off
title Generador de reportes REPORTSW
pushd "%~dp0"

REM Busca Python: primero el lanzador "py", luego "python".
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "generador_reportes.py"
    goto :fin
)

where python >nul 2>nul
if %errorlevel%==0 (
    python "generador_reportes.py"
    goto :fin
)

echo.
echo  No se encontro Python en esta computadora.
echo  Instalalo desde https://www.python.org/downloads/
echo  y marca la casilla "Add Python to PATH" durante la instalacion.
echo.
pause
popd
exit /b 1

:fin
if errorlevel 1 (
    echo.
    echo  El programa termino con un error.
    pause
)
popd
