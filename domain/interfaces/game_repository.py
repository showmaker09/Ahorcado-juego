from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.alumno import Alumno
from domain.entities.partida import Partida


class GameRepository(ABC):
    """
    Contrato de repositorio abstracto para el juego del Ahorcado.
    El dominio ignora por completo la tecnología de persistencia (MongoDB).
    """

    @abstractmethod
    def buscar_alumno_por_matricula(self, matricula: str) -> Optional[Alumno]:
        """
        Consulta la colección oficial de alumnos para validar la matrícula.
        Retorna la entidad Alumno si existe, o None si no está registrado.
        """
        pass

    @abstractmethod
    def obtener_partida_viva(self, partida_id: str = "partida_viva") -> Optional[Partida]:
        """
        Obtiene el estado actual del documento de la partida viva.
        """
        pass

    @abstractmethod
    def registrar_letra_acierto(
        self,
        partida_id: str,
        letra: str,
        nuevos_espacios: List[str],
        es_victoria: bool,
        formato_ganador: str
    ) -> bool:
        """
        Aplica atómicamente el acierto de una letra en la base de datos.
        Filtro de concurrencia: activo: True y letra no intentada ($ne).
        Actualiza: espacios_visibles, agrega a letras_intentadas ($push).
        Si es victoria: activo: False y ganador: formato_ganador ($set).
        Retorna True si el documento fue modificado efectivamente (modified_count > 0).
        """
        pass

    @abstractmethod
    def registrar_letra_fallo(
        self,
        partida_id: str,
        letra: str
    ) -> bool:
        """
        Aplica atómicamente el fallo de una letra en la base de datos.
        Filtro de concurrencia: activo: True y letra no intentada ($ne).
        Operaciones atómicas: $inc vidas_restantes: -1 y $push letra en letras_intentadas.
        Retorna True si el documento fue modificado efectivamente (modified_count > 0).
        """
        pass
