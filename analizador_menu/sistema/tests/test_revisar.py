"""Pruebas del revisor rapido.  Ejecutar con:  python -m unittest discover tests"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent          # carpeta "sistema"
PROYECTO = RAIZ.parent                                  # carpeta del programa
FIXTURES = RAIZ / "tests" / "fixtures"

REPORTE_BUENO_TXT = PROYECTO / "datos" / "6001 (3-6).txt"
REPORTE_BUENO_PDF = PROYECTO / "datos" / "6012 (17-19).pdf"
REPORTE_VACIO_PDF = FIXTURES / "6004_10_al_13.pdf"

# El revisor es un programa suelto en la raiz, sin paquete que importar.
_especificacion = importlib.util.spec_from_file_location(
    "revisar_archivos", PROYECTO / "revisar_archivos.py"
)
revisar_archivos = importlib.util.module_from_spec(_especificacion)
_especificacion.loader.exec_module(revisar_archivos)

ESTADO_OK = revisar_archivos.ESTADO_OK
ESTADO_VACIO = revisar_archivos.ESTADO_VACIO
ESTADO_NO_ABRE = revisar_archivos.ESTADO_NO_ABRE


class PruebaRevisarArchivo(unittest.TestCase):
    def test_reporte_txt_completo(self):
        registro = revisar_archivos.revisar(REPORTE_BUENO_TXT)
        self.assertEqual(registro["estado"], ESTADO_OK)
        self.assertEqual(registro["restaurante"], "6001")
        self.assertEqual(registro["periodo"], "del 03/08/2026 al 06/08/2026")

    def test_reporte_pdf_completo(self):
        registro = revisar_archivos.revisar(REPORTE_BUENO_PDF)
        self.assertEqual(registro["estado"], ESTADO_OK)
        self.assertEqual(registro["restaurante"], "6012")
        self.assertEqual(registro["periodo"], "del 17/08/2026 al 19/08/2026")

    def test_reporte_pdf_vacio(self):
        """El caso real: se abre bien, pero no trae un solo producto."""
        registro = revisar_archivos.revisar(REPORTE_VACIO_PDF)
        self.assertEqual(registro["estado"], ESTADO_VACIO)
        self.assertEqual(registro["restaurante"], "6004")
        self.assertEqual(registro["periodo"], "del 10/08/2026 al 13/08/2026")
        self.assertIn("sin un solo producto", registro["motivo"])

    def test_archivo_de_cero_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "6005 (1-4).pdf"
            ruta.touch()
            registro = revisar_archivos.revisar(ruta)
            self.assertEqual(registro["estado"], ESTADO_VACIO)
            self.assertIn("0 bytes", registro["motivo"])

    def test_pdf_corrupto(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "6006 (1-4).pdf"
            ruta.write_bytes(b"%PDF-1.4 basura")
            registro = revisar_archivos.revisar(ruta)
            self.assertEqual(registro["estado"], ESTADO_NO_ABRE)
            self.assertTrue(registro["motivo"])

    def test_txt_que_no_es_un_reporte(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "6007 (1-4).txt"
            ruta.write_text("cualquier cosa\n", encoding="utf-8")
            registro = revisar_archivos.revisar(ruta)
            self.assertEqual(registro["estado"], ESTADO_VACIO)

    def test_no_confunde_las_lineas_de_categoria_con_productos(self):
        """'   1--TEAM PLATTER' es una categoria, no un producto."""
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "6008 (1-4).txt"
            ruta.write_text(
                " 1--STARTERS\n   1--TEAM PLATTER\n"
                "Category Totals                          0.00       0.00\n",
                encoding="utf-8",
            )
            registro = revisar_archivos.revisar(ruta)
            self.assertEqual(registro["estado"], ESTADO_VACIO)
            self.assertIn("sin un solo producto", registro["motivo"])


class PruebaUtilidades(unittest.TestCase):
    def test_limpiar_ruta_con_comillas(self):
        esperado = r"C:\Users\velascoh\Desktop\Hora Bostons"
        for entrada in (f'"{esperado}"', f"'{esperado}'", f"\u201c{esperado}\u201d", esperado):
            with self.subTest(entrada=entrada):
                self.assertEqual(revisar_archivos.limpiar_ruta(entrada), esperado)

    def test_restaurante_desde_el_nombre(self):
        for nombre, esperado in [
            ("6001 (3-6).txt", "6001"),
            ("6004_10_al_13.pdf", "6004"),
            ("6012-17-19.pdf", "6012"),
            ("reporte.pdf", ""),
        ]:
            with self.subTest(nombre=nombre):
                self.assertEqual(revisar_archivos.restaurante_de(Path(nombre)), esperado)

    def test_listar_archivos_toma_txt_y_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "6001 (3-6).txt").touch()
            (carpeta / "6012 (17-19).pdf").touch()
            (carpeta / "notas.docx").touch()          # se ignora
            (carpeta / "~$temporal.pdf").touch()      # se ignora
            nombres = [p.name for p in revisar_archivos.listar_archivos(carpeta)]
            self.assertEqual(nombres, ["6001 (3-6).txt", "6012 (17-19).pdf"])


class PruebaVigilar(unittest.TestCase):
    """Modo continuo: revisa cada archivo nuevo conforme se va descargando."""

    @staticmethod
    def _correr(carpeta, pasos, diccionario=None):
        """Corre el bucle simulando 'descargo un archivo y doy Enter'.

        Cada paso es (lo que se teclea, que se descarga justo antes).
        """
        secuencia = iter(pasos)

        def entrada(_mensaje):
            orden, descargar = next(secuencia)
            descargar()
            return orden

        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = revisar_archivos.vigilar(
                Path(carpeta), diccionario or {}, leer_orden=entrada, pausa=0
            )
        return codigo, salida.getvalue()

    def _copiar(self, origen: Path, destino: Path):
        return lambda: destino.write_bytes(origen.read_bytes())

    def test_revisa_solo_los_archivos_nuevos(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "6001 (3-6).txt").write_bytes(REPORTE_BUENO_TXT.read_bytes())

            codigo, salida = self._correr(
                carpeta,
                [
                    ("", lambda: None),  # todavia no llega nada
                    ("", self._copiar(REPORTE_VACIO_PDF, carpeta / "6004 (10-13).pdf")),
                    ("salir", lambda: None),
                ],
            )

            self.assertIn("No llego ningun archivo nuevo", salida)
            self.assertIn("Reviso 1 archivo(s) nuevo(s)", salida)
            self.assertIn("6004 (10-13).pdf", salida)
            # El que ya estaba no se vuelve a revisar en cada vuelta.
            self.assertEqual(salida.count("6001 (3-6).txt"), 1)
            self.assertEqual(codigo, 1)  # quedo uno pendiente

    def test_una_re_descarga_encima_se_vuelve_a_revisar(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            malo = carpeta / "6004 (10-13).pdf"
            malo.write_bytes(REPORTE_VACIO_PDF.read_bytes())

            def redescargar_bien():
                # Mismo nombre, pero ahora el reporte si trae datos.
                malo.write_bytes(REPORTE_BUENO_PDF.read_bytes())

            codigo, salida = self._correr(
                carpeta, [("", redescargar_bien), ("salir", lambda: None)]
            )

            self.assertIn("re-descargado", salida)
            self.assertIn("TODO BIEN", salida)
            self.assertEqual(codigo, 0)  # ya quedo resuelto

    def test_avisa_de_las_descargas_a_medias(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            a_medias = carpeta / "6019 (10-13).pdf.crdownload"

            codigo, salida = self._correr(
                carpeta,
                [
                    ("", lambda: a_medias.write_bytes(b"bajando...")),
                    ("salir", lambda: None),
                ],
            )

            self.assertIn("todavia en curso", salida)
            self.assertIn("6019 (10-13).pdf.crdownload", salida)
            self.assertEqual(codigo, 1)  # no se reviso nada

    def test_la_orden_todo_revisa_de_nuevo_lo_que_ya_habia(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "6001 (3-6).txt").write_bytes(REPORTE_BUENO_TXT.read_bytes())

            codigo, salida = self._correr(
                carpeta, [("todo", lambda: None), ("salir", lambda: None)]
            )

            self.assertEqual(salida.count("6001 (3-6).txt"), 2)  # inicio + "todo"
            self.assertEqual(codigo, 0)

    def test_arranca_con_la_carpeta_vacia(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            codigo, salida = self._correr(
                carpeta,
                [
                    ("", self._copiar(REPORTE_BUENO_TXT, carpeta / "6001 (3-6).txt")),
                    ("salir", lambda: None),
                ],
            )
            self.assertIn("La carpeta esta vacia por ahora", salida)
            self.assertIn("6001 (3-6).txt", salida)
            self.assertEqual(codigo, 0)

    def test_ctrl_c_sale_con_el_resumen(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "6004 (10-13).pdf").write_bytes(REPORTE_VACIO_PDF.read_bytes())

            def interrumpir(_mensaje):
                raise KeyboardInterrupt

            salida = io.StringIO()
            with contextlib.redirect_stdout(salida):
                codigo = revisar_archivos.vigilar(
                    carpeta, {"6004": "Ciudad Del Carmen"}, leer_orden=interrumpir, pausa=0
                )

            self.assertIn("Hay que volver a descargar", salida.getvalue())
            self.assertIn("Ciudad Del Carmen", salida.getvalue())
            self.assertEqual(codigo, 1)


class PruebaProgramaCompleto(unittest.TestCase):
    """El reporte en pantalla no interesa aqui, solo el codigo de salida."""

    @staticmethod
    def _correr(argumentos: list[str]) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return revisar_archivos.main(argumentos)

    def test_devuelve_cero_cuando_todo_esta_bien(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / REPORTE_BUENO_TXT.name).write_text(
                REPORTE_BUENO_TXT.read_text(encoding="utf-8"), encoding="utf-8"
            )
            self.assertEqual(self._correr(["--carpeta", tmp]), 0)

    def test_devuelve_uno_cuando_hay_un_reporte_vacio(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / REPORTE_BUENO_TXT.name).write_text(
                REPORTE_BUENO_TXT.read_text(encoding="utf-8"), encoding="utf-8"
            )
            (Path(tmp) / REPORTE_VACIO_PDF.name).write_bytes(REPORTE_VACIO_PDF.read_bytes())
            self.assertEqual(self._correr(["--carpeta", tmp]), 1)

    def test_devuelve_uno_cuando_la_carpeta_no_trae_reportes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._correr(["--carpeta", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
