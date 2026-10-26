import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """
    Gestor de conexión a MongoDB Atlas.
    Cumple con el requisito técnico:
    MongoClient(uri, serverSelectionTimeoutMS=5000, tls=True)
    Las credenciales se obtienen estrictamente de variables de entorno.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        db_name: Optional[str] = None,
        timeout_ms: Optional[int] = None
    ):
        if not os.getenv("MONGODB_URI"):
            load_dotenv()

        self.uri = uri or os.getenv("MONGODB_URI")
        if not self.uri:
            raise ValueError(
                "La variable de entorno 'MONGODB_URI' no está configurada. "
                "Por favor defina MONGODB_URI en su archivo .env."
            )

        self.db_name = db_name or os.getenv("DB_NAME", "game_cloud")
        raw_timeout = os.getenv("SERVER_SELECTION_TIMEOUT_MS", "5000")
        try:
            self.timeout_ms = timeout_ms or int(raw_timeout)
        except ValueError:
            self.timeout_ms = 5000

        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None

    def get_database(self) -> Database:
        """
        Devuelve el objeto Database inicializando la conexión si es necesario.
        Valida conectividad mediante comando de administración 'ping'.
        """
        if self._database is None:
            self.connect()
        return self._database

    def connect(self) -> Database:
        """
        Establece la conexión con MongoDB Atlas respetando los parámetros obligatorios.
        """
        try:
            logger.info("Iniciando conexión con MongoDB Atlas...")
            self._client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=self.timeout_ms,
                tls=True,
                retryWrites=True
            )
            # Prueba de salud de conexión
            self._client.admin.command("ping")
            self._database = self._client[self.db_name]
            logger.info(f"Conexión exitosa a la base de datos: '{self.db_name}'")
            return self._database
        except ServerSelectionTimeoutError as e:
            logger.error(f"Tiempo de espera agotado al conectar a Atlas ({self.timeout_ms}ms): {e}")
            raise ConnectionError(
                f"No se pudo contactar al clúster de MongoDB Atlas (Timeout {self.timeout_ms}ms). "
                f"Verifique su conexión a internet y las credenciales."
            ) from e
        except ConnectionFailure as e:
            logger.error(f"Falla de conexión de red con MongoDB Atlas: {e}")
            raise ConnectionError(f"Error de red al conectar con MongoDB Atlas: {e}") from e
        except PyMongoError as e:
            logger.error(f"Error inesperado en PyMongo: {e}")
            raise ConnectionError(f"Fallo al inicializar cliente de MongoDB: {e}") from e

    def close(self) -> None:
        """Cierra el pool de conexiones de manera ordenada."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("Conexión a MongoDB Atlas cerrada correctamente.")
