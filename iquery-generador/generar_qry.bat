@echo off
REM ===========================================================
REM  Lanzador para Windows del generador de consultas .qry
REM  Este archivo NO contiene el programa: ejecuta
REM  generador_qry.py, que debe estar en esta misma carpeta.
REM ===========================================================
setlocal
cd /d "%~dp0"

REM Consola en UTF-8 para que los acentos no tumben el programa
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

if not exist "generador_qry.py" goto sin_programa

REM Buscar Python 3 (sin volver a lanzar el programa si algo falla)
set "PYCMD="
py -3 -c "pass" >nul 2>&1
if not errorlevel 1 set "PYCMD=py -3"
if defined PYCMD goto correr

python -c "pass" >nul 2>&1
if not errorlevel 1 set "PYCMD=python"
if defined PYCMD goto correr

python3 -c "pass" >nul 2>&1
if not errorlevel 1 set "PYCMD=python3"
if defined PYCMD goto correr

goto sin_python

:correr
%PYCMD% "generador_qry.py"
echo.
pause
exit /b 0

:sin_programa
echo No encontre "generador_qry.py" en esta carpeta:
echo    %~dp0
echo.
echo El lanzador y el programa tienen que estar juntos en la misma carpeta.
echo Si acabas de descomprimir una version nueva, revisa que no estes
echo abriendo el lanzador de una carpeta vieja.
echo.
pause
exit /b 1

:sin_python
echo No encontre Python 3 instalado en esta computadora.
echo.
echo Descargalo de https://www.python.org/downloads/
echo IMPORTANTE: al instalarlo marca la casilla "Add python.exe to PATH".
echo.
pause
exit /b 1
