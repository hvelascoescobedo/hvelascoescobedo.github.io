@echo off
REM Doble clic en Windows para abrir el generador.
cd /d "%~dp0"
py -3 generador_qry.py 2>nul || python generador_qry.py
echo.
pause
