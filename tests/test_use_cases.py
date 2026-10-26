"""Pruebas unitarias de casos de uso con Mock Repository y unittest."""
import unittest
from typing import Optional, List
from domain.entities.alumno import Alumno
from domain.entities.partida import Partida
from domain.interfaces.game_repository import GameRepository
from application.use_cases.validar_matricula import ValidarMatriculaUseCase
from application.use_cases.enviar_letra import EnviarLetraUseCase


class FakeGameRepository(GameRepository):
    def __init__(self):
        self.alumnos = {
            "24090569": Alumno(matricula="24090569", nombre_real="PEREZ MENDEZ")
        }
        self.partida = Partida(
            id="partida_viva",
            pista="Patrón de diseño",
            palabra_secreta="SINGLETON",
            espacios_visibles=["S", "I", "_", "G", "L", "E", "T", "O", "_"],
            letras_intentadas=["S", "I", "G", "L", "E", "T", "O"],
            vidas_restantes=6,
            activo=True,
            ganador=None
        )
        self.acierto_llamado = False
        self.fallo_llamado = False

    def buscar_alumno_por_matricula(self, matricula: str) -> Optional[Alumno]:
        return self.alumnos.get(matricula)

    def obtener_partida_viva(self, partida_id: str = "partida_viva") -> Optional[Partida]:
        return self.partida

    def registrar_letra_acierto(
        self,
        partida_id: str,
        letra: str,
        nuevos_espacios: List[str],
        es_victoria: bool,
        formato_ganador: str
    ) -> bool:
        self.acierto_llamado = True
        self.partida.espacios_visibles = nuevos_espacios
        self.partida.letras_intentadas.append(letra)
        if es_victoria:
            self.partida.activo = False
            self.partida.ganador = formato_ganador
        return True

    def registrar_letra_fallo(self, partida_id: str, letra: str) -> bool:
        self.fallo_llamado = True
        self.partida.vidas_restantes -= 1
        self.partida.letras_intentadas.append(letra)
        return True


class TestUseCases(unittest.TestCase):
    def setUp(self):
        self.repo = FakeGameRepository()

    def test_validar_matricula_existente(self):
        uc = ValidarMatriculaUseCase(self.repo)
        alumno = uc.ejecutar("24090569")
        self.assertIsNotNone(alumno)
        self.assertEqual(alumno.nombre_real, "PEREZ MENDEZ")

    def test_validar_matricula_inexistente(self):
        uc = ValidarMatriculaUseCase(self.repo)
        alumno = uc.ejecutar("99999999")
        self.assertIsNone(alumno)

    def test_enviar_letra_victoria(self):
        alumno = self.repo.alumnos["24090569"]
        uc = EnviarLetraUseCase(self.repo)

        # Letra final para completar SINGLETON: 'N'
        resultado = uc.ejecutar(alumno=alumno, letra="N")
        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.tipo, "VICTORIA")
        self.assertFalse(self.repo.partida.activo)
        self.assertEqual(self.repo.partida.ganador, "PEREZ MENDEZ (24090569)")

    def test_enviar_letra_fallo(self):
        alumno = self.repo.alumnos["24090569"]
        uc = EnviarLetraUseCase(self.repo)

        resultado = uc.ejecutar(alumno=alumno, letra="Z")
        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.tipo, "FALLO")
        self.assertTrue(self.repo.fallo_llamado)
        self.assertEqual(self.repo.partida.vidas_restantes, 5)

    def test_enviar_letra_repetida(self):
        alumno = self.repo.alumnos["24090569"]
        uc = EnviarLetraUseCase(self.repo)

        # 'S' ya fue intentada en la partida inicial
        resultado = uc.ejecutar(alumno=alumno, letra="S")
        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.tipo, "YA_INTENTADA")


if __name__ == "__main__":
    unittest.main()
