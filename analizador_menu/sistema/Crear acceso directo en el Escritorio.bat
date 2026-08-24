@echo off
setlocal
rem Crea en el Escritorio un acceso directo al programa, para no tener que
rem entrar a esta carpeta cada vez.
cd /d "%~dp0.."
set "CARPETA=%CD%"

powershell -NoProfile -Command "$e=(New-Object -ComObject WScript.Shell); $s=$e.CreateShortcut((([Environment]::GetFolderPath('Desktop'))+'\Buscar items.lnk')); $s.TargetPath='%CARPETA%\Buscar items.bat'; $s.WorkingDirectory='%CARPETA%'; $s.IconLocation='%SystemRoot%\System32\imageres.dll,165'; $s.Description='Buscador de ventas por item'; $s.Save()"

if errorlevel 1 goto :error
echo.
echo Listo: ya tienes "Buscar items" en el Escritorio.
echo Puedes moverlo a donde quieras; seguira apuntando a esta carpeta.
goto :fin

:error
echo.
echo No se pudo crear el acceso directo.

:fin
echo.
pause
