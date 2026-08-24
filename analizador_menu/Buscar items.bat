@echo off
setlocal
title Buscador de ventas por item
cd /d "%~dp0"

rem --- Se busca Python: primero el lanzador "py", luego "python" ---
set "PY=py -3"
py -3 --version >nul 2>&1 || set "PY=python"
%PY% --version >nul 2>&1 || goto :sin_python

rem --- Si falta openpyxl se instala solo la primera vez ---
%PY% -c "import openpyxl" >nul 2>&1 || (
    echo Preparando el programa por primera vez, espera un momento...
    %PY% -m pip install --quiet -r "sistema\requirements.txt"
)

%PY% "buscar_items.py" %*
goto :fin

:sin_python
echo.
echo No encontre Python instalado en esta computadora.
echo Descargalo de https://www.python.org/downloads/ y al instalarlo
echo marca la casilla "Add Python to PATH".

:fin
echo.
pause
