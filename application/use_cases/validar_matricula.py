import logging
from typing import Optional
from domain.entities.alumno import Alumno
from domain.interfaces.game_repository import GameRepository

logger = logging.getLogger(__name__)


class ValidarMatriculaUseCase:
    """
    Caso de uso: Validar la identidad del alumno contra la colección 'alumnos_registrados'.
    Regla 1 (Blindaje de Identidad):
      - Pedir matrícula.
      - Consultar por _id.
      - Si no existe -> denegar acceso.
      - El nombre real se obtiene solo de la base de datos.
    """

    def __init__(self, repository: GameRepository):
        self._repository = repository

    def ejecutar(self, matricula: str) -> Optional[Alumno]:
        matricula_limpia = matricula.strip()
        if not matricula_limpia:
            logger.warning("Intento de validación con matrícula vacía.")
            return None

        logger.info(f"Validando matrícula: '{matricula_limpia}'...")
        alumno = self._repository.buscar_alumno_por_matricula(matricula_limpia)
        if alumno:
            logger.info(f"Alumno autenticado: {alumno.nombre_real} ({alumno.matricula})")
        else:
            logger.warning(f"Matrícula '{matricula_limpia}' rechazada por el sistema.")
        return alumno
