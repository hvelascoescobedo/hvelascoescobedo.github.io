@echo off
setlocal

REM Ir a la carpeta de PosiTouch
cd /d C:\SC

REM Crear carpeta para reportes si no existe
if not exist C:\PosiReports mkdir C:\PosiReports

REM Ejecutar reporte VENTAS
REPORTSW 8 C 15 13 N 4 YYYYYYYYYYYYYYYYYYYYY N Y 1 N N

REM Esperar a que termine
timeout /t 10 /nobreak >nul

exit