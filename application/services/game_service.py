from typing import Optional
from domain.entities.alumno import Alumno
from domain.entities.partida import Partida
from application.use_cases.verificar_estado import VerificarEstadoUseCase
from application.use_cases.enviar_letra import EnviarLetraUseCase, ResultadoJugada


class GameService:
    """
    Servicio de aplicación para orquestar la interacción con el juego del Ahorcado.
    """

    def __init__(
        self,
        verificar_estado_uc: VerificarEstadoUseCase,
        enviar_letra_uc: EnviarLetraUseCase
    ):
        self._verificar_estado_uc = verificar_estado_uc
        self._enviar_letra_uc = enviar_letra_uc

    def consultar_partida(self, partida_id: str = "partida_viva") -> Optional[Partida]:
        """Obtiene el estado en tiempo real de la partida."""
        return self._verificar_estado_uc.ejecutar(partida_id)

    def realizar_jugada(
        self,
        alumno: Alumno,
        letra: str,
        partida_id: str = "partida_viva"
    ) -> ResultadoJugada:
        """Envía una letra a procesar de acuerdo con las reglas de concurrencia."""
        return self._enviar_letra_uc.ejecutar(alumno, letra, partida_id)
