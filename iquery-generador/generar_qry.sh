#!/usr/bin/env bash
# Lanzador del generador de .qry para iQuery.
#
# Este archivo NO contiene el programa: solo busca Python 3 y ejecuta
# 'generador_qry.py', que debe estar en esta misma carpeta.
# Todos los mensajes y preguntas viven en generador_qry.py.
#
# Uso:  ./generar_qry.sh      (o doble clic en generar_qry.command en macOS)

set -u

# Trabajar siempre desde la carpeta donde vive este script
CARPETA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CARPETA" || exit 1

# El programa debe estar junto a este lanzador
if [ ! -f "$CARPETA/generador_qry.py" ]; then
    echo "No encontré 'generador_qry.py' en esta carpeta:"
    echo "   $CARPETA"
    echo
    echo "El lanzador y el programa tienen que estar juntos en la misma carpeta."
    echo "Si acabas de descomprimir una versión nueva, revisa que no estés"
    echo "abriendo el lanzador de una carpeta vieja."
    read -r -p "Presiona Enter para cerrar..."
    exit 1
fi

# Buscar Python 3 (python3, python o el lanzador py de Windows)
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1 && python -c 'import sys; sys.exit(0 if sys.version_info[0]==3 else 1)' 2>/dev/null; then
    PYTHON="python"
elif command -v py >/dev/null 2>&1; then
    PYTHON="py -3"
else
    echo "No encontré Python 3 instalado."
    echo "Descárgalo de https://www.python.org/downloads/ y vuelve a intentar."
    read -r -p "Presiona Enter para cerrar..."
    exit 1
fi

$PYTHON "$CARPETA/generador_qry.py"
ESTADO=$?

echo
read -r -p "Presiona Enter para cerrar esta ventana..."
exit $ESTADO
