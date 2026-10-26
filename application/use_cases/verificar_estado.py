import logging
from typing import Optional
from domain.entities.partida import Partida
from domain.interfaces.game_repository import GameRepository

logger = logging.getLogger(__name__)


class VerificarEstadoUseCase:
    """
    Caso de uso: Consultar en tiempo real el estado global de la partida viva.
    """

    def __init__(self, repository: GameRepository):
        self._repository = repository

    def ejecutar(self, partida_id: str = "partida_viva") -> Optional[Partida]:
        logger.debug(f"Consultando estado de la partida '{partida_id}'...")
        return self._repository.obtener_partida_viva(partida_id)
