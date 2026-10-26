import logging
from dataclasses import dataclass
from typing import Optional
from domain.entities.alumno import Alumno
from domain.entities.partida import Partida
from domain.interfaces.game_repository import GameRepository

logger = logging.getLogger(__name__)


@dataclass
class ResultadoJugada:
    """
    Objeto de transferencia que describe el resultado de un intento de jugada.
    """
    exito: bool
    mensaje: str
    tipo: str  # 'ACIERTO', 'VICTORIA', 'FALLO', 'YA_INTENTADA', 'PARTIDA_TERMINADA', 'CONCURRENCIA_PERDIDA', 'ERROR_FORMATO'
    partida: Optional[Partida] = None


class EnviarLetraUseCase:
    """
    Caso de uso: Procesar el intento de una letra por parte de un alumno.
    Garantiza el cumplimiento estricto de:
      - Regla 2: Vidas globales atómicas ($inc).
      - Regla 3: Protección anti-spam ($ne en update).
      - Regla 4: Victoria por concurrencia pura (activo: true, primer impacto gana).
      - Regla 5: Operadores obligatorios ($set, $inc, $push).
    """

    def __init__(self, repository: GameRepository):
        self._repository = repository

    def ejecutar(self, alumno: Alumno, letra: str, partida_id: str = "partida_viva") -> ResultadoJugada:
        letra_limpia = letra.strip().upper()

        # Validación sintáctica
        if len(letra_limpia) != 1 or not (letra_limpia.isalpha() or letra_limpia == 'Ñ'):
            return ResultadoJugada(
                exito=False,
                mensaje="Debe ingresar exactamente una sola letra válida (A-Z).",
                tipo="ERROR_FORMATO"
            )

        # 1. Obtener estado actual
        partida = self._repository.obtener_partida_viva(partida_id)
        if not partida:
            return ResultadoJugada(
                exito=False,
                mensaje=f"No se encontró la partida con id '{partida_id}'.",
                tipo="ERROR_PARTIDA"
            )

        # 2. Validar si la partida sigue en curso
        if not partida.esta_activa:
            ganador = partida.ganador or "Sin ganador registrado"
            return ResultadoJugada(
                exito=False,
                mensaje=f"La partida ha finalizado. Ganador oficial: {ganador}",
                tipo="PARTIDA_TERMINADA",
                partida=partida
            )

        # 3. Validación previa local (si ya fue intentada)
        if partida.ya_intentada(letra_limpia):
            return ResultadoJugada(
                exito=False,
                mensaje=f"La letra '{letra_limpia}' ya ha sido intentada anteriormente.",
                tipo="YA_INTENTADA",
                partida=partida
            )

        # 4. Determinar si es acierto o fallo
        if partida.contiene_letra(letra_limpia):
            nuevos_espacios = partida.calcular_nuevos_espacios(letra_limpia)
            es_victoria = partida.esta_completada_con(nuevos_espacios)

            # Impacto atómico en BD
            impacto = self._repository.registrar_letra_acierto(
                partida_id=partida.id,
                letra=letra_limpia,
                nuevos_espacios=nuevos_espacios,
                es_victoria=es_victoria,
                formato_ganador=alumno.formato_ganador
            )

            # Releer estado actualizado
            partida_actualizada = self._repository.obtener_partida_viva(partida_id)

            if impacto:
                if es_victoria:
                    logger.info(f"¡VICTORIA REGISTRADA para {alumno.formato_ganador}!")
                    return ResultadoJugada(
                        exito=True,
                        mensaje=f"¡VICTORIA! Has completado la palabra '{partida.palabra_secreta}' como primer impacto.",
                        tipo="VICTORIA",
                        partida=partida_actualizada
                    )
                else:
                    return ResultadoJugada(
                        exito=True,
                        mensaje=f"¡Acierto! La letra '{letra_limpia}' está en la palabra.",
                        tipo="ACIERTO",
                        partida=partida_actualizada
                    )
            else:
                # Regla 4: Concurrencia pura. Modified count fue 0.
                if partida_actualizada and not partida_actualizada.activo:
                    return ResultadoJugada(
                        exito=False,
                        mensaje=f"Otro compañero completó la palabra primero en el nodo primario: {partida_actualizada.ganador}.",
                        tipo="CONCURRENCIA_PERDIDA",
                        partida=partida_actualizada
                    )
                else:
                    return ResultadoJugada(
                        exito=False,
                        mensaje=f"La letra '{letra_limpia}' fue enviada concurrentemente por otro cliente casi al mismo tiempo.",
                        tipo="YA_INTENTADA",
                        partida=partida_actualizada
                    )

        else:
            # Letra incorrecta (Fallo)
            impacto = self._repository.registrar_letra_fallo(
                partida_id=partida.id,
                letra=letra_limpia
            )

            partida_actualizada = self._repository.obtener_partida_viva(partida_id)

            if impacto:
                vidas = partida_actualizada.vidas_restantes if partida_actualizada else (partida.vidas_restantes - 1)
                return ResultadoJugada(
                    exito=True,
                    mensaje=f"Letra '{letra_limpia}' incorrecta. Se ha restado 1 vida global (quedan {vidas}).",
                    tipo="FALLO",
                    partida=partida_actualizada
                )
            else:
                return ResultadoJugada(
                    exito=False,
                    mensaje=f"La letra '{letra_limpia}' ya había sido registrada por otro cliente.",
                    tipo="YA_INTENTADA",
                    partida=partida_actualizada
                )
