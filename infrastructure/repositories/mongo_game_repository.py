import os
import logging
from typing import Optional, List
from pymongo.database import Database
from pymongo.errors import PyMongoError

from domain.entities.alumno import Alumno
from domain.entities.partida import Partida
from domain.interfaces.game_repository import GameRepository
from infrastructure.database.mongo_client import MongoDBConnection

logger = logging.getLogger(__name__)


class MongoGameRepository(GameRepository):
    """
    Implementación en MongoDB Atlas del repositorio del juego.
    Contiene la lógica exclusiva de operadores atómicos ($set, $inc, $push)
    y filtros de concurrencia ($ne, activo: true).
    """

    def __init__(
        self,
        db_connection: MongoDBConnection,
        game_col_name: Optional[str] = None,
        alumnos_col_name: Optional[str] = None
    ):
        self._db_conn = db_connection
        self.game_col_name = game_col_name or os.getenv("GAME_COLLECTION", "ahorcado_retos")
        self.alumnos_col_name = alumnos_col_name or os.getenv("ALUMNOS_COLLECTION", "alumnos_registrados")

    @property
    def _db(self) -> Database:
        return self._db_conn.get_database()

    def buscar_alumno_por_matricula(self, matricula: str) -> Optional[Alumno]:
        """
        Consulta la colección 'alumnos_registrados' por '_id' (matrícula).
        Blindaje de identidad: Si el alumno no existe, retorna None.
        """
        matricula_limpia = str(matricula).strip()
        try:
            col = self._db[self.alumnos_col_name]
            doc = col.find_one({"_id": matricula_limpia})
            if not doc:
                logger.warning(f"Matrícula '{matricula_limpia}' no encontrada en '{self.alumnos_col_name}'.")
                return None

            return Alumno(
                matricula=str(doc.get("_id", matricula_limpia)),
                nombre_real=str(doc.get("nombre_real", "SIN NOMBRE"))
            )
        except PyMongoError as e:
            logger.error(f"Error al consultar alumno con matrícula '{matricula_limpia}': {e}")
            raise ConnectionError(f"Error de red al validar la matrícula: {e}") from e

    def obtener_partida_viva(self, partida_id: str = "partida_viva") -> Optional[Partida]:
        """
        Obtiene el estado actual del documento de la partida en Atlas.
        """
        try:
            col = self._db[self.game_col_name]
            doc = col.find_one({"_id": partida_id})
            if not doc:
                logger.warning(f"Documento de partida '{partida_id}' no encontrado en '{self.game_col_name}'.")
                return None

            return Partida(
                id=str(doc.get("_id", partida_id)),
                pista=str(doc.get("pista", "")),
                palabra_secreta=str(doc.get("palabra_secreta", "")),
                espacios_visibles=list(doc.get("espacios_visibles", [])),
                letras_intentadas=list(doc.get("letras_intentadas", [])),
                vidas_restantes=int(doc.get("vidas_restantes", 6)),
                activo=bool(doc.get("activo", False)),
                ganador=doc.get("ganador")
            )
        except PyMongoError as e:
            logger.error(f"Error al obtener partida '{partida_id}': {e}")
            raise ConnectionError(f"Error de red al consultar el estado de la partida: {e}") from e

    def registrar_letra_acierto(
        self,
        partida_id: str,
        letra: str,
        nuevos_espacios: List[str],
        es_victoria: bool,
        formato_ganador: str
    ) -> bool:
        """
        Actualización atómica de letra correcta.
        Filtros de concurrencia:
          - activo: True
          - letras_intentadas: {"$ne": letra} (Anti-spam)
        Operadores:
          - $set: actualiza espacios_visibles (y activo: False, ganador si es victoria)
          - $push: agrega letra a letras_intentadas
        """
        letra_norm = letra.strip().upper()
        filter_doc = {
            "_id": partida_id,
            "activo": True,
            "letras_intentadas": {"$ne": letra_norm}
        }

        if es_victoria:
            update_doc = {
                "$set": {
                    "espacios_visibles": nuevos_espacios,
                    "activo": False,
                    "ganador": formato_ganador
                },
                "$push": {
                    "letras_intentadas": letra_norm
                }
            }
        else:
            update_doc = {
                "$set": {
                    "espacios_visibles": nuevos_espacios
                },
                "$push": {
                    "letras_intentadas": letra_norm
                }
            }

        try:
            col = self._db[self.game_col_name]
            result = col.update_one(filter_doc, update_doc)
            logger.info(
                f"Acierto enviado para '{letra_norm}' en '{partida_id}'. "
                f"Matched: {result.matched_count}, Modified: {result.modified_count}"
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error al registrar acierto de letra '{letra_norm}': {e}")
            raise ConnectionError(f"Error de red al enviar jugada: {e}") from e

    def registrar_letra_fallo(
        self,
        partida_id: str,
        letra: str
    ) -> bool:
        """
        Actualización atómica de letra incorrecta.
        Filtros de concurrencia:
          - activo: True
          - letras_intentadas: {"$ne": letra} (Anti-spam: solo descuenta vida la primera vez)
        Operadores:
          - $inc: decrementa vidas_restantes en -1
          - $push: agrega letra a letras_intentadas
        """
        letra_norm = letra.strip().upper()
        filter_doc = {
            "_id": partida_id,
            "activo": True,
            "letras_intentadas": {"$ne": letra_norm}
        }
        update_doc = {
            "$inc": {
                "vidas_restantes": -1
            },
            "$push": {
                "letras_intentadas": letra_norm
            }
        }

        try:
            col = self._db[self.game_col_name]
            result = col.update_one(filter_doc, update_doc)
            logger.info(
                f"Fallo enviado para '{letra_norm}' en '{partida_id}'. "
                f"Matched: {result.matched_count}, Modified: {result.modified_count}"
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error al registrar fallo de letra '{letra_norm}': {e}")
            raise ConnectionError(f"Error de red al enviar jugada: {e}") from e
