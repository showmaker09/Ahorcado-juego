"""Pruebas unitarias para las entidades del dominio con unittest estándar."""
import unittest
from domain.entities.alumno import Alumno
from domain.entities.partida import Partida


class TestDomainEntities(unittest.TestCase):
    def test_alumno_formato_ganador(self):
        alumno = Alumno(matricula="24090569", nombre_real="PEREZ MENDEZ")
        self.assertEqual(alumno.formato_ganador, "PEREZ MENDEZ (24090569)")

    def test_partida_contiene_letra(self):
        partida = Partida(
            id="partida_viva",
            pista="Patrón de diseño",
            palabra_secreta="SINGLETON",
            espacios_visibles=["_", "_", "_", "_", "_", "_", "_", "_", "_"],
            letras_intentadas=[],
            vidas_restantes=6,
            activo=True
        )
        self.assertTrue(partida.contiene_letra("s"))
        self.assertTrue(partida.contiene_letra("S"))
        self.assertFalse(partida.contiene_letra("Z"))

    def test_partida_calcular_nuevos_espacios(self):
        partida = Partida(
            id="partida_viva",
            pista="Patrón de diseño",
            palabra_secreta="SINGLETON",
            espacios_visibles=["_", "_", "_", "_", "_", "_", "_", "_", "_"],
            letras_intentadas=[],
            vidas_restantes=6,
            activo=True
        )
        nuevos = partida.calcular_nuevos_espacios("N")
        # 'N' está en el índice 2 y 8 de SINGLETON
        self.assertEqual(nuevos[2], "N")
        self.assertEqual(nuevos[8], "N")
        self.assertEqual(nuevos[0], "_")

    def test_partida_esta_completada(self):
        partida = Partida(
            id="partida_viva",
            pista="Patrón de diseño",
            palabra_secreta="SINGLETON",
            espacios_visibles=["S", "I", "N", "G", "L", "E", "T", "O", "_"],
            letras_intentadas=["S", "I", "N", "G", "L", "E", "T", "O"],
            vidas_restantes=6,
            activo=True
        )
        nuevos = partida.calcular_nuevos_espacios("N")
        self.assertTrue(partida.esta_completada_con(nuevos))

    def test_partida_ya_intentada(self):
        partida = Partida(
            id="partida_viva",
            pista="Patrón de diseño",
            palabra_secreta="SINGLETON",
            espacios_visibles=["_", "_", "_", "_", "_", "_", "_", "_", "_"],
            letras_intentadas=["A", "B", "C"],
            vidas_restantes=6,
            activo=True
        )
        self.assertTrue(partida.ya_intentada("a"))
        self.assertTrue(partida.ya_intentada("B"))
        self.assertFalse(partida.ya_intentada("Z"))


if __name__ == "__main__":
    unittest.main()
