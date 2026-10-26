from typing import Optional
from domain.entities.alumno import Alumno
from application.use_cases.validar_matricula import ValidarMatriculaUseCase


class AuthService:
    """
    Servicio de autenticación para coordinar la validación y blindaje de identidad de los alumnos.
    """

    def __init__(self, validar_matricula_uc: ValidarMatriculaUseCase):
        self._validar_matricula_uc = validar_matricula_uc

    def autenticar(self, matricula: str) -> Optional[Alumno]:
        """
        Valida la matrícula contra la colección oficial de MongoDB Atlas.
        Retorna el objeto Alumno con su nombre oficial si es válido, de lo contrario None.
        """
        return self._validar_matricula_uc.ejecutar(matricula)
