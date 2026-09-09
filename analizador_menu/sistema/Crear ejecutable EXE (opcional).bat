@echo off
setlocal
title Crear el ejecutable
rem Genera "Buscar items.exe" y "Revisar archivos.exe" para que los
rem programas corran aunque la computadora no tenga Python.
rem Solo hay que correrlo una vez.
cd /d "%~dp0.."

set "PY=py -3"
py -3 --version >nul 2>&1 || set "PY=python"
%PY% --version >nul 2>&1 || goto :sin_python

echo Instalando lo necesario (PyInstaller)...
%PY% -m pip install --quiet -r "sistema\requirements.txt" pyinstaller || goto :error

echo Creando el ejecutable, esto tarda unos minutos...
%PY% -m PyInstaller --noconfirm --onefile --console ^
    --name "Buscar items" ^
    --paths "%CD%\sistema" ^
    --hidden-import pypdf ^
    --add-data "%CD%\sistema\Diccionario_restaurantes.xlsx;." ^
    --distpath "sistema\_build\dist" ^
    --workpath "sistema\_build\work" ^
    --specpath "sistema\_build" ^
    "%CD%\buscar_items.py" || goto :error

copy /y "sistema\_build\dist\Buscar items.exe" "Buscar items.exe" >nul || goto :error

echo Creando el revisor de archivos...
%PY% -m PyInstaller --noconfirm --onefile --console ^
    --name "Revisar archivos" ^
    --hidden-import pypdf ^
    --add-data "%CD%\sistema\Diccionario_restaurantes.xlsx;." ^
    --distpath "sistema\_build\dist" ^
    --workpath "sistema\_build\work" ^
    --specpath "sistema\_build" ^
    "%CD%\revisar_archivos.py" || goto :error

copy /y "sistema\_build\dist\Revisar archivos.exe" "Revisar archivos.exe" >nul || goto :error
echo.
echo Listo: se crearon "Buscar items.exe" y "Revisar archivos.exe" aqui.
echo Dejalos junto a las carpetas datos y resultados.
goto :fin

:sin_python
echo.
echo Para crear el ejecutable si hace falta tener Python instalado.
echo Descargalo de https://www.python.org/downloads/
goto :fin

:error
echo.
echo Algo fallo al crear el ejecutable. Revisa el mensaje de arriba.

:fin
echo.
pause
