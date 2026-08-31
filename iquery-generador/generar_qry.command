#!/usr/bin/env bash
# Doble clic en macOS para abrir el generador en la Terminal.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/generar_qry.sh"
